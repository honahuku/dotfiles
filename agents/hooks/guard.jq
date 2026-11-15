include "command-policy";
include "hook-settings-policy";

# 許可を先に返すと後続の拒否判定を隠すため、拒否結果だけを出力する。
([deny_sensitive_commands, deny_hook_settings] | first) // empty
