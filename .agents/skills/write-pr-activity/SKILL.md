---
name: write-pr-activity
description: 今日作業したGitHub PRを根拠に基づいて列挙し、本人のPR対応と依頼されたレビューに分ける。今日のPR作業一覧を求められたときに使用する。
---

# List today's PR activity

Use this skill when asked to list GitHub pull requests that the user worked on today. The result contains only PRs with evidence of the user's work during the requested day.

## Set the time window

- Determine the current date, time, and the user's time zone from the conversation or available client context. Ask if the time zone cannot be established; do not infer it from the machine or repository.
- Use the interval from local midnight, inclusive, through the time the information is collected. Convert those boundaries to absolute timestamps when querying GitHub or local history.
- Judge activity by each event's timestamp, not by a PR's current `updated_at` value. Recheck the cutoff time before producing the list.

## Find and verify candidate PRs

1. Identify the authenticated GitHub account and discover the repositories available to the current connection. Do not limit the initial search to a presumed organization or repository. Use available read-only GitHub tools; if needed, use authenticated `gh` read commands or `gh api --method GET`.
2. Search for candidate PRs using the user's activity events, PR search, and commit search. When available, read the authenticated user's events with `GET /users/{username}/events`. Cover GitHub and Git activity such as commits, pushes, PR creation or updates, comments and replies, merges, approvals, change requests, and review work. Search broadly for PRs authored by the user and PRs where the user was asked to review. Search results and event feeds find candidates; they do not prove that work occurred during the window.
3. Treat the Events API as a discovery source only. GitHub says event delivery is not real-time and can be delayed from 30 seconds to 6 hours, so cross-check it against PR searches and each candidate's records. Follow pagination for event, comment, review, and search results where available. Record when permissions, result limits, or unavailable repositories leave coverage incomplete.
4. For each candidate, verify the canonical PR title, number, URL, and author. Inspect the PR timeline, issue comments and replies, review comments and replies, submitted reviews, commits, and merge or review-request events. Attribute an event only when its actor and timestamp match the user and the time window.
5. Inspect locally available repositories and worktrees for commits and available reflog evidence in the same time window. Correlate commit SHAs and branches with PRs; local Git history alone does not prove which PR an operation belongs to. State which local repositories were available for inspection.
6. For review work not submitted to GitHub, use same-day chat history or other available records that show the review was actually started or performed. A message quoting older history is not evidence of a same-day action; check the timestamp of the work itself.

GitHub's [Events API](https://docs.github.com/en/rest/activity/events), [PR timeline API](https://docs.github.com/en/rest/issues/timeline), [PR search filters](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests), and [REST pagination guidance](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api) describe the relevant records and their limits.

## Classify verified work

### レビュイー(自分)

Include a PR the user authored or handled on the author side, with at least one verified action in the time window. Examples include creating or updating the PR, pushing or committing changes associated with it, replying to review feedback, or merging it. Do not infer author-side work from the PR merely being open or updated by someone else.

### レビュワー(メンバーからの依頼)

Include another person's PR only when there is evidence that a member requested the review and the user actually worked on it in the time window. Evidence can be a submitted review, review comment or reply, or same-day records showing substantive review work. A review request by itself does not qualify. Reading a PR as background for another task does not qualify.

Do not guess an operation or role when the evidence is unclear. Do not describe reading a review as an approval; report approval only when a submitted review records the `APPROVED` state. Deduplicate PRs within each category by canonical repository and PR number.

## Format the result

Keep the response focused on the two categories and PR links. Add one short scope line with the local date, time zone, collection cutoff, and material gaps in the GitHub, local-repository, or chat history inspected.

見出しとPR行は次の形式にする。

```markdown
確認範囲: <日付> 00:00–<取得時刻> (<タイムゾーン>)。<確認できた範囲と不足>

## レビュイー(自分)
- [<正式なPRタイトル>](https://github.com/<owner>/<repo>/pull/<number>#top)#<number>

## レビュワー(メンバーからの依頼)
- [<正式なPRタイトル>](https://github.com/<owner>/<repo>/pull/<number>#top)#<number>
```

Use `- なし` for an empty category. If an unresolved candidate could materially change the list, state it separately as `要確認` and identify the missing evidence; do not put it in a completed-work list.

All collection is read-only. Do not commit, push, create or update PRs, post or reply to comments, submit reviews, approve, request changes, or merge.
