// list-window-ids.swift
// List CGWindowIDs + bounds for all visible windows of a named app.
// Usage: swift list-window-ids.swift                 # list Terminal windows
//        swift list-window-ids.swift "Google Chrome" # list Chrome windows
// Output: one line per window: <id>|<windowName>|<x>,<y>|<w>x<h>

import Cocoa
import CoreGraphics

let target = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "Terminal"

let infoList = CGWindowListCopyWindowInfo(
    [.optionOnScreenOnly, .excludeDesktopElements],
    kCGNullWindowID
) as? [[String: Any]] ?? []

var found = 0
for info in infoList {
    let ownerName = info[kCGWindowOwnerName as String] as? String ?? ""
    let windowName = info[kCGWindowName as String] as? String ?? ""
    let windowID = info[kCGWindowNumber as String] as? Int ?? 0
    let bounds = info[kCGWindowBounds as String] as? [String: Any] ?? [:]
    if ownerName == target {
        let x = bounds["X"] as? Double ?? 0
        let y = bounds["Y"] as? Double ?? 0
        let w = bounds["Width"] as? Double ?? 0
        let h = bounds["Height"] as? Double ?? 0
        print("\(windowID)|\(windowName)|\(Int(x)),\(Int(y))|\(Int(w))x\(Int(h))")
        found += 1
    }
}

if found == 0 {
    FileHandle.standardError.write("No visible windows for owner=\"\(target)\"\n".data(using: .utf8)!)
    exit(1)
}
