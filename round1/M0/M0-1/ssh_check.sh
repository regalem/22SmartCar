#!/usr/bin/env bash
# =============================================================================
#  M0-1 远程登录自检脚本
#  用法：
#    bash ssh_check.sh                  # 只检查工具、公钥、权限、known_hosts
#    bash ssh_check.sh user@host        # 额外测试免密登录与 scp 上传
#  说明：
#    - 只做检查，不会伪造 known_hosts，也不会修改任何配置；
#    - 退出码 0 = 没有 FAIL（WARN 需现场向考官说明）；1 = 有 FAIL。
# =============================================================================

set -u

PASS=0
FAIL=0
WARN=0

if [ -t 1 ]; then
    C_OK=$'\033[32m'; C_BAD=$'\033[31m'; C_WARN=$'\033[33m'; C_OFF=$'\033[0m'
else
    C_OK=''; C_BAD=''; C_WARN=''; C_OFF=''
fi

ok()   { printf '%s[PASS]%s %s\n' "$C_OK" "$C_OFF" "$1"; PASS=$((PASS + 1)); }
bad()  { printf '%s[FAIL]%s %s\n' "$C_BAD" "$C_OFF" "$1"; FAIL=$((FAIL + 1)); }
warn() { printf '%s[WARN]%s %s\n' "$C_WARN" "$C_OFF" "$1"; WARN=$((WARN + 1)); }
info() { printf '       %s\n' "$1"; }

echo "=============================================================="
echo "  M0-1 远程登录自检  ($(date '+%F %T'))"
echo "=============================================================="

# ---------------------------------------------------------------- 1. 工具
echo
echo "--- 1. 远程工具 ---"
for t in ssh scp ssh-keygen rsync; do
    if command -v "$t" >/dev/null 2>&1; then
        ok "$t -> $(command -v "$t")"
    else
        bad "缺少 $t（sudo apt install -y openssh-client rsync）"
    fi
done

# ---------------------------------------------------------------- 2. 公钥
echo
echo "--- 2. SSH 公钥 ---"
KEY=""
for k in "$HOME/.ssh/id_ed25519.pub" "$HOME/.ssh/id_rsa.pub"; do
    if [ -f "$k" ]; then
        KEY="$k"
        break
    fi
done
if [ -n "$KEY" ]; then
    ok "公钥存在：$KEY"
    info "$(cut -d' ' -f1,3 "$KEY" 2>/dev/null || true)"
else
    bad "未发现 SSH 公钥（ssh-keygen -t ed25519 -C 'you@example.com'）"
fi

# ---------------------------------------------------------------- 3. 权限
echo
echo "--- 3. 目录与文件权限 ---"
if [ -d "$HOME/.ssh" ]; then
    MODE="$(stat -c '%a' "$HOME/.ssh" 2>/dev/null || echo '?')"
    if [ "$MODE" = "700" ]; then
        ok "~/.ssh 权限 = 700"
    else
        warn "~/.ssh 权限 = $MODE（应为 700：chmod 700 ~/.ssh）"
    fi
else
    warn "~/.ssh 不存在（还没有生成过密钥）"
fi

AK="$HOME/.ssh/authorized_keys"
if [ -f "$AK" ]; then
    MODE="$(stat -c '%a' "$AK" 2>/dev/null || echo '?')"
    if [ "$MODE" = "600" ]; then
        ok "authorized_keys 权限 = 600"
    else
        warn "authorized_keys 权限 = $MODE（应为 600：chmod 600 ~/.ssh/authorized_keys）"
    fi
else
    info "本机没有 authorized_keys（只作为客户端登录别的主机时属正常）"
fi

# ---------------------------------------------------------------- 4. 已知主机
echo
echo "--- 4. 真实连接痕迹 ---"
if [ -s "$HOME/.ssh/known_hosts" ]; then
    ok "known_hosts 非空（$(wc -l < "$HOME/.ssh/known_hosts" | tr -d ' ') 条记录）"
else
    warn "known_hosts 为空：还没有真实登录过任何主机（ssh <user>@<host>）"
fi

# ---------------------------------------------------------------- 5. 可选：真实登录
if [ "$#" -ge 1 ]; then
    HOST="$1"
    echo
    echo "--- 5. 免密登录测试：$HOST ---"
    if ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new \
        "$HOST" 'printf M0-1-SSH-OK' 2>/dev/null | grep -q 'M0-1-SSH-OK'; then
        ok "免密登录成功：$HOST"
        TMP_REMOTE="/tmp/.m0_1_scp_test_$$"
        if scp -q -o BatchMode=yes -o ConnectTimeout=5 "$0" "$HOST:$TMP_REMOTE" 2>/dev/null; then
            ok "scp 上传成功"
            ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOST" "rm -f '$TMP_REMOTE'" >/dev/null 2>&1 || true
        else
            bad "scp 上传失败（检查目标目录写权限与 sshd 配置）"
        fi
    else
        bad "免密登录失败（检查公钥、权限、sshd 与网络；可加 -v 查看原因）"
    fi
else
    echo
    info "提示：bash ssh_check.sh <user>@<host>   # 额外测试登录与 scp"
fi

# ---------------------------------------------------------------- 汇总
echo
echo "=============================================================="
printf '  汇总: %sPASS=%d%s  %sFAIL=%d%s  %sWARN=%d%s\n' \
    "$C_OK" "$PASS" "$C_OFF" "$C_BAD" "$FAIL" "$C_OFF" "$C_WARN" "$WARN" "$C_OFF"
echo "=============================================================="
if [ "$FAIL" -eq 0 ]; then
    echo "  远程登录链路: 通过（WARN 项请现场向考官说明）"
    exit 0
fi
echo "  远程登录链路: 未通过 —— 请修复 FAIL 项后重跑"
exit 1