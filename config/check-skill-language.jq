# コード・識別子・リンクの題名は維持し、説明文と説明フィールドを検査する。
def japanese: test("[\\p{Hiragana}\\p{Katakana}\\p{Han}]");
split("\n")
| reduce range(0; length) as $i (
    {lines: ., fence: false, frontmatter: false, errors: []};
    .lines[$i] as $line
    | if ($line | test("^\\s*(```|~~~)")) then
        .fence = (.fence | not)
      elif .fence then .
      elif $line == "---" and $i == 0 then .frontmatter = true
      elif $line == "---" and .frontmatter then .frontmatter = false
      elif ($line | test("^\\s*(description|short_description|default_prompt):")) then
        if ($line | japanese) then .
        else .errors += [$i + 1] end
      elif .frontmatter then .
      elif ($line | test("^\\s*(interface|policy|display_name|icon_small|icon_large|allow_implicit_invocation):")) then .
      else
        ($line
          | gsub("\\[[^\\]]*\\]\\([^)]*\\)"; "")
          | gsub("`[^`]*`"; "")
          | gsub("https?://[^[:space:]]+"; "")) as $prose
        | if ($prose | japanese) then .
          elif ($prose | test("^#{1,6}\\s+[A-Za-z]"))
            or ([$prose | scan("[A-Za-z]{2,}")] | length >= 4)
          then .errors += [$i + 1]
          else . end
      end
  )
| if (.errors | length) == 0 then empty
  else error("説明文を日本語にする: 行 " + (.errors | map(tostring) | join(", ")))
  end
