"""Descriptor-anchored filesystem and executable safety primitives."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import selectors
import signal
import stat
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Self


class FsafetyError(RuntimeError):
    """A trusted descriptor or bounded execution operation failed."""


class UnsupportedCapability(FsafetyError):
    """This platform cannot execute a retained descriptor safely."""


CHILD_ENV = {
    "LC_ALL": "C",
    "LANG": "C",
    "TZ": "UTC",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
}


def _flags(directory: bool = False) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    return flags


def _parts(path: Path) -> tuple[str, ...]:
    text = os.fspath(path)
    if not os.path.isabs(text) or "\x00" in text:
        raise FsafetyError("path must be an absolute path without NUL")
    raw = text.split(os.sep)
    if any(item in (".", "..") for item in raw):
        raise FsafetyError("path contains traversal component")
    return tuple(item for item in raw if item)


@dataclass
class DirectoryHandle:
    """A retained directory descriptor and its physical identity."""

    fd: int
    device: int
    inode: int
    display_path: Path

    @property
    def path(self) -> Path:
        return self.display_path

    @property
    def st_dev(self) -> int:
        return self.device

    @property
    def st_ino(self) -> int:
        return self.inode

    @classmethod
    def from_fd(cls, fd: int, display_path: Path) -> DirectoryHandle:
        info = os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode):
            raise FsafetyError(f"not a directory: {display_path}")
        return cls(fd, info.st_dev, info.st_ino, display_path)

    def verify_identity(self) -> None:
        info = os.fstat(self.fd)
        if (info.st_dev, info.st_ino) != (self.device, self.inode):
            raise FsafetyError("retained directory identity changed")

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _open_absolute(path: Path) -> DirectoryHandle:
    current = os.open(os.sep, _flags(directory=True))
    display = Path(os.sep)
    try:
        for component in _parts(path):
            try:
                nxt = os.open(component, _flags(directory=True), dir_fd=current)
            except OSError as exc:
                # macOS exposes /var (and /tmp) as symlinks into /private.
                # Resolve only these fixed OS aliases; authority-bearing
                # application components still require O_NOFOLLOW.
                if (
                    sys.platform == "darwin"
                    and component in {"var", "tmp"}
                    and exc.errno in (errno.ELOOP, errno.ENOTDIR)
                ):
                    nxt = os.open("private", _flags(directory=True), dir_fd=current)
                    private = os.open(component, _flags(directory=True), dir_fd=nxt)
                    os.close(nxt)
                    nxt = private
                else:
                    raise
            os.close(current)
            current = nxt
            display /= component
        return DirectoryHandle.from_fd(current, path)
    except BaseException:
        os.close(current)
        raise


def open_trusted_tree(root: Path, path: Path) -> DirectoryHandle:
    """Open *path* beneath *root* one non-following component at a time."""

    root = Path(root)
    path = Path(path)
    root_parts = _parts(root)
    path_parts = _parts(path)
    if len(path_parts) < len(root_parts) or path_parts[: len(root_parts)] != root_parts:
        raise FsafetyError("path escapes trusted root")
    root_handle = _open_absolute(root)
    current = root_handle.fd
    try:
        for component in path_parts[len(root_parts) :]:
            try:
                nxt = os.open(component, _flags(directory=True), dir_fd=current)
            except OSError as exc:
                if (
                    sys.platform == "darwin"
                    and component in {"var", "tmp"}
                    and exc.errno in (errno.ELOOP, errno.ENOTDIR)
                ):
                    alias_root = os.open(
                        "private", _flags(directory=True), dir_fd=current
                    )
                    try:
                        nxt = os.open(
                            component, _flags(directory=True), dir_fd=alias_root
                        )
                    finally:
                        os.close(alias_root)
                else:
                    raise
            os.close(current)
            current = nxt
        root_handle.fd = -1
        root_handle.close()
        return DirectoryHandle.from_fd(current, path)
    except BaseException:
        if current >= 0:
            os.close(current)
        root_handle.fd = -1
        raise


def open_descendant(root: DirectoryHandle, path: Path) -> DirectoryHandle:
    """Open a path beneath a retained root descriptor component by component."""

    root.verify_identity()
    path = Path(path)
    root_parts = _parts(root.display_path)
    path_parts = _parts(path)
    if len(path_parts) < len(root_parts) or path_parts[: len(root_parts)] != root_parts:
        raise FsafetyError("path escapes retained trusted root")
    current = os.dup(root.fd)
    try:
        for component in path_parts[len(root_parts) :]:
            nxt = os.open(component, _flags(directory=True), dir_fd=current)
            os.close(current)
            current = nxt
        return DirectoryHandle.from_fd(current, path)
    except BaseException:
        os.close(current)
        raise


def _read_fd(fd: int, *, limit: int = 64 * 1024 * 1024) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > limit:
            raise FsafetyError("captured file exceeds size limit")
        chunks.append(chunk)


@dataclass
class VerifiedExecutable:
    """An executable bound to an open descriptor and measured digest."""

    fd: int
    binding: object
    device: int
    inode: int
    measured_sha256: str

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


def _fd_sha256(fd: int, *, limit: int = 64 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    offset = 0
    while True:
        chunk = os.pread(fd, 1024 * 1024, offset)
        if not chunk:
            return digest.hexdigest()
        offset += len(chunk)
        if offset > limit:
            raise FsafetyError("captured file exceeds size limit")
        digest.update(chunk)


def _verify_executable_identity(executable: VerifiedExecutable) -> None:
    info = os.fstat(executable.fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or (info.st_dev, info.st_ino) != (executable.device, executable.inode)
    ):
        raise FsafetyError("retained executable identity changed")
    try:
        path_info = os.stat(
            os.fspath(Path(executable.binding.path)),
            follow_symlinks=False,
        )
    except OSError as exc:
        raise FsafetyError("executable pathname is unavailable") from exc
    if (path_info.st_dev, path_info.st_ino) != (
        executable.device,
        executable.inode,
    ):
        raise FsafetyError("executable pathname was replaced")
    if _fd_sha256(executable.fd) != executable.measured_sha256:
        raise FsafetyError("retained executable digest changed")


@dataclass
class _DarwinRootControlledExecutable:
    """A verified executable whose full namespace is root-controlled."""

    executable: VerifiedExecutable

    @property
    def path(self) -> Path:
        return Path(self.executable.binding.path)

    def verify_identity(self) -> None:
        _verify_executable_identity(self.executable)
        if not _darwin_path_is_root_controlled(self.path):
            raise FsafetyError("Darwin root-controlled executable path changed")


def _darwin_path_is_root_controlled(path: Path) -> bool:
    """Return whether this UID cannot replace or modify the executable path."""

    if os.geteuid() == 0:
        return False
    current = os.open(os.sep, _flags(directory=True))
    try:
        root_info = os.fstat(current)
        if (
            root_info.st_uid != 0
            or stat.S_IMODE(root_info.st_mode) & 0o022
            or os.access(
                ".", os.W_OK, dir_fd=current, effective_ids=True
            )
        ):
            return False
        parts = _parts(path)
        for component in parts[:-1]:
            nxt = os.open(component, _flags(directory=True), dir_fd=current)
            os.close(current)
            current = nxt
            info = os.fstat(current)
            if (
                info.st_uid != 0
                or stat.S_IMODE(info.st_mode) & 0o022
                or os.access(
                    ".", os.W_OK, dir_fd=current, effective_ids=True
                )
            ):
                return False
        info = os.stat(parts[-1], dir_fd=current, follow_symlinks=False)
        return (
            info.st_uid == 0
            and not stat.S_IMODE(info.st_mode) & 0o022
            and not os.access(
                parts[-1],
                os.W_OK,
                dir_fd=current,
                effective_ids=True,
                follow_symlinks=False,
            )
        )
    except OSError:
        return False
    finally:
        os.close(current)


def open_verified_executable(binding: object) -> VerifiedExecutable:
    path = Path(binding.path)
    _parts(path)
    parent = path.parent
    name = path.name
    with open_trusted_tree(Path("/"), parent) as parent_handle:
        fd = os.open(name, _flags(), dir_fd=parent_handle.fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not (info.st_mode & 0o111):
            raise FsafetyError("executable is not a regular executable file")
        os.lseek(fd, 0, os.SEEK_SET)
        digest = hashlib.sha256(_read_fd(fd)).hexdigest()
        os.lseek(fd, 0, os.SEEK_SET)
        if digest != binding.sha256:
            raise FsafetyError("binary SHA-256 does not match binding")
        path_info = os.stat(os.fspath(path), follow_symlinks=False)
        if (path_info.st_dev, path_info.st_ino) != (info.st_dev, info.st_ino):
            raise FsafetyError("executable pathname was replaced")
        return VerifiedExecutable(fd, binding, info.st_dev, info.st_ino, digest)
    except BaseException:
        os.close(fd)
        raise


def descriptor_exec_supported() -> bool:
    """Return whether this host has a tested retained-descriptor exec path."""

    if sys.platform == "darwin":
        return False
    if hasattr(os, "fexecve"):
        return True
    try:
        return bool(ctypes.CDLL(None).fexecve)
    except (AttributeError, OSError):
        return sys.platform.startswith("linux") and os.path.exists("/proc/self/fd")


def _exec_fd(fd: int, argv: list[str], env: dict[str, str]) -> None:
    if hasattr(os, "fexecve"):
        os.fexecve(fd, argv, env)  # type: ignore[attr-defined]
    if sys.platform.startswith("linux") and os.path.exists("/proc/self/fd"):
        os.set_inheritable(fd, True)
        os.execve(f"/proc/self/fd/{fd}", argv, env)
    libc = ctypes.CDLL(None, use_errno=True)
    function = getattr(libc, "fexecve", None)
    if function is None:
        raise UnsupportedCapability("descriptor execution is unavailable")
    function.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.POINTER(ctypes.c_char_p),
    ]
    function.restype = ctypes.c_int
    encoded_argv = [item.encode() for item in argv] + [None]
    encoded_env = [f"{key}={value}".encode() for key, value in env.items()] + [None]
    result = function(
        fd,
        (ctypes.c_char_p * len(encoded_argv))(*encoded_argv),
        (ctypes.c_char_p * len(encoded_env))(*encoded_env),
    )
    if result < 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))


@dataclass(frozen=True)
class ExecutionResult:
    stdout: bytes
    stderr: bytes
    returncode: int


def _run_verified_argv(
    executable: VerifiedExecutable,
    argv: Sequence[str],
    cwd: DirectoryHandle,
    timeout: float = 30.0,
    *,
    max_output: int = 4 * 1024 * 1024,
    darwin_strategy: _DarwinRootControlledExecutable | None = None,
) -> ExecutionResult:
    """Supervise an already-certified executable strategy."""

    if timeout <= 0:
        raise ValueError("timeout must be positive")
    cwd.verify_identity()
    _verify_executable_identity(executable)
    if darwin_strategy is not None:
        darwin_strategy.verify_identity()
    out_read, out_write = os.pipe()
    err_read, err_write = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(out_read)
            os.close(err_read)
            os.dup2(out_write, 1)
            os.dup2(err_write, 2)
            os.close(out_write)
            os.close(err_write)
            cwd.verify_identity()
            os.fchdir(cwd.fd)
            command = [Path(executable.binding.path).name, *map(str, argv)]
            if darwin_strategy is None:
                os.set_inheritable(executable.fd, True)
                _exec_fd(executable.fd, command, dict(CHILD_ENV))
            else:
                darwin_strategy.verify_identity()
                os.execve(os.fspath(darwin_strategy.path), command, dict(CHILD_ENV))
        # The child must report every pre-exec failure and exit fail-closed;
        # narrowing this catch could strand descriptors or skip the 127 exit.
        except BaseException as exc:  # noqa: BLE001
            try:
                os.write(2, f"descriptor execution failed: {exc}\n".encode())
            finally:
                os._exit(127)
    os.close(out_write)
    os.close(err_write)
    for fd in (out_read, err_read):
        os.set_blocking(fd, False)
    selector = selectors.DefaultSelector()
    selector.register(out_read, selectors.EVENT_READ, "out")
    selector.register(err_read, selectors.EVENT_READ, "err")
    buffers = {"out": bytearray(), "err": bytearray()}
    deadline = __import__("time").monotonic() + timeout
    timed_out = False
    status = 0
    child_done = False
    try:
        while selector.get_map() or not child_done:
            if not child_done:
                waited_pid, waited_status = os.waitpid(pid, os.WNOHANG)
                if waited_pid == pid:
                    child_done = True
                    status = waited_status
            remaining = deadline - __import__("time").monotonic()
            if remaining <= 0:
                if not child_done:
                    timed_out = True
                    os.kill(pid, signal.SIGKILL)
                    _, status = os.waitpid(pid, 0)
                    child_done = True
                break
            for key, _ in selector.select(min(remaining, 0.1)):
                try:
                    data = os.read(key.fd, 65536)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    data = b""
                if data:
                    buffers[key.data].extend(data)
                    if sum(map(len, buffers.values())) > max_output:
                        os.kill(pid, signal.SIGKILL)
                        os.waitpid(pid, 0)
                        raise FsafetyError("child output exceeds limit")
                else:
                    selector.unregister(key.fd)
                    os.close(key.fd)
        if not child_done:
            _, status = os.waitpid(pid, 0)
    finally:
        for key in list(selector.get_map().values()):
            selector.unregister(key.fd)
            os.close(key.fd)
    if timed_out:
        returncode = -signal.SIGKILL
    elif os.WIFEXITED(status):
        returncode = os.WEXITSTATUS(status)
    else:
        returncode = -os.WTERMSIG(status)
    _verify_executable_identity(executable)
    if darwin_strategy is not None:
        darwin_strategy.verify_identity()
    if timed_out:
        raise TimeoutError("verified executable timed out")
    return ExecutionResult(bytes(buffers["out"]), bytes(buffers["err"]), returncode)


class GitProbe(Enum):
    """The complete fixed read-only Git command surface."""

    VERSION = "version"
    WORKTREE_LIST = "worktree-list"
    COMMON_DIR = "common-dir"


def _git_probe_argv(probe: GitProbe) -> tuple[str, ...]:
    if type(probe) is not GitProbe:
        raise ValueError("unsupported Git probe")
    if probe is GitProbe.VERSION:
        return ("--version",)
    if probe is GitProbe.WORKTREE_LIST:
        return ("worktree", "list", "--porcelain")
    return ("rev-parse", "--git-common-dir")


def run_verified_git_probe(
    executable: VerifiedExecutable,
    probe: GitProbe,
    cwd: DirectoryHandle,
) -> ExecutionResult:
    """Run one fixed Git probe from a verified executable and directory.

    Darwin has no ``fexecve``/``execveat`` and rejects executable ``/dev/fd``
    paths.  Only a root-owned path that the effective UID cannot write is safe
    enough for its finite pathname execution surface.  User-owned Git binaries
    remain unsupported.
    """

    strategy: _DarwinRootControlledExecutable | None = None
    if sys.platform == "darwin":
        _verify_executable_identity(executable)
        if not _darwin_path_is_root_controlled(Path(executable.binding.path)):
            raise UnsupportedCapability(
                "Darwin read-only execution requires a root-controlled path"
            )
        strategy = _DarwinRootControlledExecutable(executable)
    elif not descriptor_exec_supported():
        raise UnsupportedCapability("descriptor execution is unavailable on this host")
    return _run_verified_argv(
        executable,
        _git_probe_argv(probe),
        cwd,
        timeout=30,
        darwin_strategy=strategy,
    )


def fixed_control_root() -> Path:
    import pwd

    home = pwd.getpwuid(os.geteuid()).pw_dir
    return Path(home) / ".local/state/beads-convergence/control"


def validate_fixed_control_root() -> DirectoryHandle:
    """Open the compiled per-user control root after validating every part."""

    path = fixed_control_root()
    parts = _parts(path)
    home_parts = _parts(Path(path).parents[3])
    current = os.open(os.sep, _flags(directory=True))
    try:
        for index, component in enumerate(parts):
            try:
                nxt = os.open(component, _flags(directory=True), dir_fd=current)
            except OSError as exc:
                if (
                    sys.platform == "darwin"
                    and component in {"var", "tmp"}
                    and exc.errno in (errno.ELOOP, errno.ENOTDIR)
                ):
                    alias_root = os.open(
                        "private", _flags(directory=True), dir_fd=current
                    )
                    try:
                        nxt = os.open(
                            component, _flags(directory=True), dir_fd=alias_root
                        )
                    finally:
                        os.close(alias_root)
                else:
                    raise
            info = os.fstat(nxt)
            if index + 1 >= len(home_parts) and (
                info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o700
            ):
                os.close(nxt)
                raise FsafetyError(f"unsafe fixed control root component: {component}")
            os.close(current)
            current = nxt
        return DirectoryHandle.from_fd(current, path)
    except BaseException:
        os.close(current)
        raise


open_control_root = validate_fixed_control_root
