#!/opt/homebrew/bin/bash

set -euo pipefail
IFS=$'\n\t'

# Comprehensive Lines of Code Counter
# Counts everything: application logic, tests, CI/CD, documentation, observability, internal tooling
# Excludes: venv/, node_modules/, .git/, __pycache__, tmp/

echo "📊 Lines of Code Count (Comprehensive — All File Types)"
echo "======================================================="

# Utility to normalize glob scopes used for functional area summaries
normalize_scope_glob() {
    local scope="$1"

    if [[ -z "$scope" ]]; then
        echo ""
        return
    fi

    local glob="$scope"

    if [[ "$glob" != ./* && "$glob" != /* ]]; then
        glob="./${glob#./}"
    fi

    if [[ "$glob" == */ ]]; then
        glob="${glob}*"
    elif [[ "$glob" != *\** && "$glob" != *\?* ]]; then
        glob="${glob%/}/*"
    fi

    echo "$glob"
}

# Identify whether a file path should be considered documentation
is_doc_file() {
    local path="$1"
    local ext="$2"

    case "${ext,,}" in
        md|mdx|rst|adoc|ipynb)
            return 0
            ;;
    esac
    return 1
}

# Identify whether a file path should be considered test code
is_test_file() {
    local path="$1"
    local ext="$2"

    local path_lc="${path,,}"
    if [[ "$path_lc" == *"/tests/"* \
        || "$path_lc" == *"/test/"* \
        || "$path_lc" == *"/testing/"* \
        || "$path_lc" == *"/__tests__/"* \
        || "$path_lc" == *"/__test__/"* \
        || "$path_lc" == *"/spec/"* \
        || "$path_lc" == *"/specs/"* \
        || "$path_lc" == *"/integration_tests/"* \
        || "$path_lc" == *"/integration-test/"* \
        || "$path_lc" == *"/qa/"* ]]; then
        return 0
    fi

    local filename="${path##*/}"
    local filename_lc="${filename,,}"

    if [[ "$filename_lc" == test_* ]]; then
        return 0
    fi

    case "$filename_lc" in
        *_test."${ext}"|*_tests."${ext}"|*_spec."${ext}")
            return 0
            ;;
        *.test."${ext}"|*.tests."${ext}"|*.spec."${ext}"|*.unit."${ext}"|*.integration."${ext}"|*.e2e."${ext}")
            return 0
            ;;
    esac

    return 1
}

declare -a LANGUAGE_SPECS=(
    "py|🐍 Python (.py)"
    "pyi|🐍 Python Stubs (.pyi)"
    "pyx|🐍 Cython (.pyx)"
    "pxd|🐍 Cython Declarations (.pxd)"
    "js|🌟 JavaScript (.js)"
    "mjs|✨ JavaScript Modules (.mjs)"
    "cjs|📦 CommonJS (.cjs)"
    "jsx|⚛️ React JSX (.jsx)"
    "ts|🌀 TypeScript (.ts)"
    "tsx|🧩 TypeScript JSX (.tsx)"
    "cts|🌀 TypeScript (.cts)"
    "mts|🌀 TypeScript (.mts)"
    "vue|🗂️ Vue Single File (.vue)"
    "svelte|🔥 Svelte (.svelte)"
    "astro|🌌 Astro (.astro)"
    "html|🌐 HTML (.html)"
    "htm|🌐 HTML (.htm)"
    "css|🎨 CSS (.css)"
    "scss|🎨 SCSS (.scss)"
    "sass|🎨 SASS (.sass)"
    "less|🎨 LESS (.less)"
    "styl|🎨 Stylus (.styl)"
    "json|🧾 JSON (.json)"
    "jsonc|🧾 JSONC (.jsonc)"
    "yaml|🧾 YAML (.yaml)"
    "yml|🧾 YAML (.yml)"
    "toml|🧾 TOML (.toml)"
    "ini|🧾 INI (.ini)"
    "cfg|🧾 Config (.cfg)"
    "conf|🧾 Config (.conf)"
    "xml|🧾 XML (.xml)"
    "xsd|🧾 XML Schema (.xsd)"
    "xsl|🧾 XSL (.xsl)"
    "sql|🗄️ SQL (.sql)"
    "graphql|🧬 GraphQL (.graphql)"
    "gql|🧬 GraphQL (.gql)"
    "prisma|🗄️ Prisma (.prisma)"
    "proto|🔌 Protobuf (.proto)"
    "rb|💎 Ruby (.rb)"
    "php|🐘 PHP (.php)"
    "go|🐹 Go (.go)"
    "rs|🦀 Rust (.rs)"
    "java|☕ Java (.java)"
    "kt|📱 Kotlin (.kt)"
    "kts|📱 Kotlin Script (.kts)"
    "swift|🕊️ Swift (.swift)"
    "cs|#️⃣ C# (.cs)"
    "fs|🧠 F# (.fs)"
    "fsx|🧠 F# Script (.fsx)"
    "scala|🛠️ Scala (.scala)"
    "clj|🌿 Clojure (.clj)"
    "cljs|🌿 ClojureScript (.cljs)"
    "groovy|🛠️ Groovy (.groovy)"
    "dart|🎯 Dart (.dart)"
    "r|📊 R (.r)"
    "jl|🔬 Julia (.jl)"
    "hs|📐 Haskell (.hs)"
    "ex|⚙️ Elixir (.ex)"
    "exs|⚙️ Elixir Script (.exs)"
    "erl|⚙️ Erlang (.erl)"
    "lua|🌙 Lua (.lua)"
    "pl|🐪 Perl (.pl)"
    "pm|🐪 Perl Module (.pm)"
    "ps1|🪟 PowerShell (.ps1)"
    "sh|🐚 Shell (.sh)"
    "bash|🐚 Bash (.bash)"
    "zsh|🐚 Zsh (.zsh)"
    "fish|🐚 Fish (.fish)"
    "bat|🪟 Batch (.bat)"
    "cmd|🪟 Command (.cmd)"
    "make|🛠️ Make (.make)"
    "mk|🛠️ Make (.mk)"
    "cmake|🛠️ CMake (.cmake)"
    "gradle|🛠️ Gradle (.gradle)"
    "c|🔧 C (.c)"
    "cc|⚙️ C++ (.cc)"
    "cpp|⚙️ C++ (.cpp)"
    "cxx|⚙️ C++ (.cxx)"
    "h|📄 Header (.h)"
    "hh|📄 Header (.hh)"
    "hpp|📄 Header (.hpp)"
    "inl|📄 Inline Header (.inl)"
    "ipp|📄 Inline Header (.ipp)"
    "mm|🍎 Objective-C++ (.mm)"
    "m|🍎 Objective-C (.m)"
    "cshtml|🌐 Razor (.cshtml)"
    "md|📝 Markdown (.md)"
    "mdx|📝 MDX (.mdx)"
    "rst|📝 ReStructuredText (.rst)"
    "adoc|📝 AsciiDoc (.adoc)"
    "ipynb|📓 Jupyter (.ipynb)"
    "nix|🧪 Nix (.nix)"
    "tf|🌍 Terraform (.tf)"
    "tfvars|🌍 Terraform Vars (.tfvars)"
    "hcl|🌍 HCL (.hcl)"
)

declare -A LANGUAGE_LABELS=()
declare -A PROD_COUNTS=()
declare -A TEST_COUNTS=()
declare -A DOCS_COUNTS=()
declare -a ORDERED_EXTS=()
declare -a ACTIVE_LANGUAGE_EXTS=()

for spec in "${LANGUAGE_SPECS[@]}"; do
    IFS='|' read -r ext label <<< "$spec"
    ORDERED_EXTS+=("$ext")
    LANGUAGE_LABELS["$ext"]="$label"
done

declare -a FIND_NAME_ARGS=()
for ext in "${ORDERED_EXTS[@]}"; do
    if (( ${#FIND_NAME_ARGS[@]} == 0 )); then
        FIND_NAME_ARGS+=( -iname "*.${ext}" )
    else
        FIND_NAME_ARGS+=( -o -iname "*.${ext}" )
    fi
done

declare -a FIND_CMD=( find . -type f )
if (( ${#FIND_NAME_ARGS[@]} > 0 )); then
    FIND_CMD+=( "(" "${FIND_NAME_ARGS[@]}" ")" )
else
    echo "📚 Language Breakdown:"
    echo "  No language extensions configured."
    exit 0
fi

FIND_CMD+=(
    ! -path "*/node_modules/*"
    ! -path "*/.git/*"
    ! -path "*/venv/*"
    ! -path "*/__pycache__/*"
    ! -path "./tmp/*"
    -print0
)

declare -a FILE_PATHS=()
declare -a FILE_EXTS=()
declare -a FILE_LINES=()
declare -a FILE_MODES=()

while IFS= read -r -d '' file; do
    ext="${file##*.}"
    ext="${ext,,}"

    if [[ -z ${LANGUAGE_LABELS["$ext"]+x} ]]; then
        continue
    fi

    lines=$(wc -l < "$file" 2>/dev/null || echo 0)
    lines=${lines//[[:space:]]/}
    if [[ -z "$lines" ]]; then
        lines=0
    fi

    mode="prod"
    if is_test_file "$file" "$ext"; then
        mode="test"
    elif is_doc_file "$file" "$ext"; then
        mode="docs"
    fi

    if [[ "$mode" == "test" ]]; then
        current_test=${TEST_COUNTS["$ext"]:-0}
        TEST_COUNTS["$ext"]=$((current_test + lines))
    elif [[ "$mode" == "docs" ]]; then
        current_docs=${DOCS_COUNTS["$ext"]:-0}
        DOCS_COUNTS["$ext"]=$((current_docs + lines))
    else
        current_prod=${PROD_COUNTS["$ext"]:-0}
        PROD_COUNTS["$ext"]=$((current_prod + lines))
    fi

    FILE_PATHS+=("$file")
    FILE_EXTS+=("$ext")
    FILE_LINES+=("$lines")
    FILE_MODES+=("$mode")
done < <("${FIND_CMD[@]}")

for ext in "${ORDERED_EXTS[@]}"; do
    prod_value=${PROD_COUNTS["$ext"]:-0}
    test_value=${TEST_COUNTS["$ext"]:-0}
    docs_value=${DOCS_COUNTS["$ext"]:-0}
    if (( prod_value + test_value + docs_value > 0 )); then
        ACTIVE_LANGUAGE_EXTS+=("$ext")
    fi
done

echo "📚 Language Breakdown:"
if (( ${#ACTIVE_LANGUAGE_EXTS[@]} > 0 )); then
    for ext in "${ORDERED_EXTS[@]}"; do
        prod_value=${PROD_COUNTS["$ext"]:-0}
        test_value=${TEST_COUNTS["$ext"]:-0}
        docs_value=${DOCS_COUNTS["$ext"]:-0}
        total_value=$((prod_value + test_value + docs_value))
        if (( total_value == 0 )); then
            continue
        fi
        label=${LANGUAGE_LABELS["$ext"]}
        echo "$label:"
        printf "  Production:    %7d lines\n" "$prod_value"
        printf "  Test:          %7d lines\n" "$test_value"
        printf "  Documentation: %7d lines\n" "$docs_value"
    done
else
    echo "  No source files found for the configured extensions."
fi

# Summary
echo ""
echo "📋 Summary:"

total_prod=0
total_test=0
total_docs=0
for ext in "${ORDERED_EXTS[@]}"; do
    prod_value=${PROD_COUNTS["$ext"]:-0}
    test_value=${TEST_COUNTS["$ext"]:-0}
    docs_value=${DOCS_COUNTS["$ext"]:-0}
    total_prod=$((total_prod + prod_value))
    total_test=$((total_test + test_value))
    total_docs=$((total_docs + docs_value))
done

total_all=$((total_prod + total_test + total_docs))

echo "  Production:    $total_prod lines (application, config, tooling)"
echo "  Test:          $total_test lines"
echo "  Documentation: $total_docs lines (markdown, planning, specs)"
echo "  ─────────────────────────────"
echo "  TOTAL:         $total_all lines"

if [[ $total_all -gt 0 ]]; then
    test_pct=$(awk -v test="$total_test" -v all="$total_all" 'BEGIN {if (all > 0) printf "%.1f", test * 100 / all; else print "0"}')
    docs_pct=$(awk -v docs="$total_docs" -v all="$total_all" 'BEGIN {if (all > 0) printf "%.1f", docs * 100 / all; else print "0"}')
    echo "  Test share:  ${test_pct}%  |  Docs share: ${docs_pct}%"
fi

echo ""
echo "🎯 Codebase by Functional Area:"
echo "==============================="

# Count major functional areas (production and/or docs)
# Third arg: "prod" (default), "docs", or "both"
count_functional_area() {
    local pattern="$1"
    local name="$2"
    local modes="${3:-prod}"

    local scope_glob
    scope_glob=$(normalize_scope_glob "$pattern")

    local total=0
    local -a languages_to_scan=()
    local -A area_counts=()

    if (( ${#ACTIVE_LANGUAGE_EXTS[@]} > 0 )); then
        languages_to_scan=("${ACTIVE_LANGUAGE_EXTS[@]}")
    else
        languages_to_scan=("${ORDERED_EXTS[@]}")
    fi

    local -A allowed_exts=()
    for ext in "${languages_to_scan[@]}"; do
        allowed_exts["$ext"]=1
    done

    for idx in "${!FILE_PATHS[@]}"; do
        local mode="${FILE_MODES[$idx]}"
        case "$modes" in
            prod)    [[ "$mode" != "prod" ]] && continue ;;
            docs)    [[ "$mode" != "docs" ]] && continue ;;
            both)    [[ "$mode" != "prod" && "$mode" != "docs" ]] && continue ;;
            *)       [[ "$mode" != "prod" ]] && continue ;;
        esac

        local ext="${FILE_EXTS[$idx]}"
        if [[ -z ${allowed_exts["$ext"]+x} ]]; then
            continue
        fi

        local path="${FILE_PATHS[$idx]}"
        if [[ -n "$scope_glob" ]]; then
            case "$path" in
                $scope_glob) ;;
                *) continue ;;
            esac
        fi

        local lines=${FILE_LINES[$idx]}
        area_counts["$ext"]=$(( ${area_counts["$ext"]:-0} + lines ))
        total=$((total + lines))
    done

    if (( total > 0 )); then
        local -a segments=()
        for ext in "${languages_to_scan[@]}"; do
            local count=${area_counts["$ext"]:-0}
            if (( count > 0 )); then
                segments+=("${ext}:${count}")
            fi
        done

        local joined=""
        if (( ${#segments[@]} > 0 )); then
            joined=$(printf ", %s" "${segments[@]}")
            joined=${joined:2}
        fi

        if [[ -n "$joined" ]]; then
            printf "  %-20s: %6d lines (%s)\n" "$name" "$total" "$joined"
        else
            printf "  %-20s: %6d lines\n" "$name" "$total"
        fi
    fi
}

# Major functional areas (production + documentation)
count_functional_area "./$PROJECT_ROOT/" "Core Application"
count_functional_area "./scripts/" "Automation Scripts"
count_functional_area "./.claude/" "AI Assistant"
count_functional_area "./orchestration/" "Task Management"
count_functional_area "./prototype*/" "Prototypes"
count_functional_area "./testing_*/" "Test Infrastructure"
count_functional_area "./.github/" "CI/CD Config" "both"
count_functional_area "./roadmap/" "Planning & Roadmap Docs" "docs"
count_functional_area "./docs/" "Documentation" "docs"
count_functional_area "./skills/" "Skills & Tooling" "both"

echo ""
echo "ℹ️  Exclusions:"
echo "  • Virtual environment (venv/)"
echo "  • Node modules, git files"
echo "  • __pycache__, tmp/"
echo "  • Everything else is counted (app, tests, CI/CD, docs, tooling)"
