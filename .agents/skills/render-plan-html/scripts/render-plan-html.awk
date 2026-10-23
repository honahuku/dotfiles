#!/usr/bin/awk -f

function escape_html(value, escaped) {
  escaped = value
  gsub(/&/, "\\&amp;", escaped)
  gsub(/</, "\\&lt;", escaped)
  gsub(/>/, "\\&gt;", escaped)
  gsub(/\"/, "\\&#34;", escaped)
  return escaped
}

function trim(value) {
  gsub(/^[ \t]+|[ \t]+$/, "", value)
  return value
}

function inline_html(value) {
  return escape_html(value)
}

function close_list() {
  if (list_open) {
    print "</ul>"
    list_open = 0
  }
}

function close_table() {
  if (table_open) {
    print "</tbody></table>"
    table_open = 0
    table_header_done = 0
  }
}

function close_section() {
  close_list()
  close_table()
  if (section_open) {
    print "</section>"
    section_open = 0
  }
}

function section_class(title, lowered) {
  lowered = tolower(title)
  if (lowered ~ /目的|purpose/) return "purpose"
  if (lowered ~ /進捗|status|progress/) return "progress"
  if (lowered ~ /作業|task|work|実装/) return "work"
  if (lowered ~ /依存|dependenc/) return "dependencies"
  if (lowered ~ /意思決定|decision/) return "decisions"
  if (lowered ~ /発見|finding|discover/) return "findings"
  if (lowered ~ /リスク|risk/) return "risks"
  if (lowered ~ /検証|validat|test|verify/) return "verification"
  return "general"
}

function print_table_row(line, tag, body, count, cells, cell_index) {
  body = line
  sub(/^[ \t]*\|/, "", body)
  sub(/\|[ \t]*$/, "", body)
  count = split(body, cells, /\|/)
  print "<tr>"
  for (cell_index = 1; cell_index <= count; cell_index++) {
    print "<" tag ">" inline_html(trim(cells[cell_index])) "</" tag ">"
  }
  print "</tr>"
}

BEGIN {
  in_code = 0
  list_open = 0
  table_open = 0
  table_header_done = 0
  section_open = 0
  section_level = 0
  print "<!doctype html>"
  print "<html lang=\"ja\" data-renderer=\"render-plan-html\" data-source-sha256=\"" escape_html(source_sha256) "\">"
  print "<head>"
  print "<meta charset=\"utf-8\">"
  print "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
  print "<title>Plan: " escape_html(source_name) "</title>"
  print "<style>"
  print ":root{color-scheme:light dark;--bg:#f5f7fb;--fg:#172033;--muted:#5b6578;--card:#fff;--line:#dbe1eb;--accent:#3867d6;--done:#16835b}"
  print "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 system-ui,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif}"
  print ".hero{padding:3rem max(1rem,calc((100vw - 1000px)/2));background:linear-gradient(135deg,#182848,#4b6cb7);color:#fff}.hero h1{margin:.2rem 0;font-size:clamp(1.8rem,4vw,3rem)}.eyebrow{margin:0;text-transform:uppercase;letter-spacing:.16em;font-size:.75rem;opacity:.8}.meta{margin:.35rem 0;font-size:.85rem;overflow-wrap:anywhere;color:#e2e8ff}.meta code{color:inherit}"
  print "main{max-width:1000px;margin:2rem auto;padding:0 1rem}.notice{padding:.8rem 1rem;border:1px solid var(--line);border-radius:.6rem;background:var(--card);color:var(--muted);font-size:.9rem}article{margin-top:1rem}section{margin:1.5rem 0;padding:1.2rem 1.4rem;border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:.6rem;background:var(--card)}"
  print "h1,h2,h3,h4,h5,h6{line-height:1.3}h1{font-size:2rem}h2{font-size:1.6rem}h3{font-size:1.3rem}pre{padding:1rem;overflow:auto;border-radius:.5rem;background:#111827;color:#e5e7eb}code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}ul{padding-left:1.5rem}.task-list{list-style:none;padding-left:0}.task-list li{display:flex;gap:.6rem;align-items:flex-start}.task-list input{margin-top:.45rem;accent-color:var(--done)}.task-list .done span{text-decoration:line-through;color:var(--muted)}blockquote{margin:1rem 0;padding:.5rem 1rem;border-left:4px solid var(--line);color:var(--muted)}table{width:100%;border-collapse:collapse;display:block;overflow:auto}th,td{padding:.55rem .7rem;border:1px solid var(--line);text-align:left;vertical-align:top}th{background:color-mix(in srgb,var(--accent) 12%,var(--card))}"
  print "@media(prefers-color-scheme:dark){:root{--bg:#101522;--fg:#e8edf7;--muted:#a8b2c5;--card:#182131;--line:#344157}}"
  print "</style>"
  print "</head><body>"
  print "<header class=\"hero\"><p class=\"eyebrow\">Plan</p><h1>" escape_html(source_name) "</h1>"
  print "<p class=\"meta\">元のMarkdown: <code>" escape_html(source_path) "</code></p>"
  print "<p class=\"meta\">入力SHA-256: <code>" escape_html(source_sha256) "</code></p>"
  print "<p class=\"meta\">生成時刻: " escape_html(generated_at) "</p></header>"
  print "<main><p class=\"notice\">このページはMarkdown planから生成されています。編集対象は元のMarkdownです。</p><article>"
}

{
  line = $0

  if (line ~ /^[ \t]*```/) {
    close_list()
    close_table()
    if (!in_code) {
      print "<pre><code>"
      in_code = 1
    } else {
      print "</code></pre>"
      in_code = 0
    }
    next
  }

  if (in_code) {
    print escape_html(line)
    next
  }

  if (line ~ /^[ \t]*$/) {
    close_list()
    close_table()
    next
  }

  if (line ~ /^[ \t]*\|.*\|[ \t]*$/) {
    close_list()
    if (!table_open) {
      print "<table><tbody>"
      table_open = 1
    }
    if (line ~ /^[ \t]*\|[ \t]*:?-+[ \t]*\|([ \t]*:?-+[ \t]*\|)+[ \t]*$/) {
      next
    }
    if (!table_header_done) {
      print_table_row(line, "th")
      table_header_done = 1
    } else {
      print_table_row(line, "td")
    }
    next
  }

  close_table()

  if (line ~ /^#{1,6}[ \t]+/) {
    close_list()
    heading = line
    match(heading, /^#+/)
    level = RLENGTH
    sub(/^#+[ \t]+/, "", heading)
    if (section_open && level <= section_level) {
      close_section()
    }
    if (level <= 2) {
      section_class_name = section_class(heading)
      print "<section class=\"section-" section_class_name "\">"
      section_open = 1
      section_level = level
    }
    print "<h" level " id=\"section-" NR "\">" inline_html(heading) "</h" level ">"
    next
  }

  if (line ~ /^[ \t]*-[ \t]+\[[ xX]\][ \t]+/) {
    if (!list_open) {
      print "<ul class=\"task-list\">"
      list_open = 1
    }
    checked = line ~ /^[ \t]*-[ \t]+\[[xX]\]/
    sub(/^[ \t]*-[ \t]+\[[ xX]\][ \t]+/, "", line)
    state = checked ? " checked" : ""
    class_name = checked ? "done" : "todo"
    print "<li class=\"" class_name "\"><input type=\"checkbox\" disabled" state "><span>" inline_html(line) "</span></li>"
    next
  }

  if (line ~ /^[ \t]*[-*+][ \t]+/) {
    if (!list_open) {
      print "<ul>"
      list_open = 1
    }
    sub(/^[ \t]*[-*+][ \t]+/, "", line)
    print "<li>" inline_html(line) "</li>"
    next
  }

  close_list()
  if (line ~ /^>[ \t]?/) {
    sub(/^>[ \t]?/, "", line)
    print "<blockquote>" inline_html(line) "</blockquote>"
    next
  }
  print "<p>" inline_html(line) "</p>"
}

END {
  close_list()
  close_table()
  if (section_open) {
    print "</section>"
  }
  if (in_code) {
    print "render-plan-html: コードブロックが閉じられていません" > "/dev/stderr"
    exit 2
  }
  print "</article></main></body></html>"
}
