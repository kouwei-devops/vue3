#!/bin/bash

# -------------------------------
# Lustre quota 转 JSON 并 POST
# -------------------------------

# 测试用模拟 Lustre 数据（本地调试可用）
quota_output=$(cat <<'EOF'
/phadcloud/home      root  615.7G      0k      0k       - 1143453       0       0       -
/phadcloud/home       501  13.32M      0k      0k       -     870     [0]     [0]       -
/phadcloud/home       502  460.7M      0k      0k       -    1506     [0]     [0]       -
EOF
)

# 逐行发送
while read -r line; do
    [[ -z "$line" ]] && continue
    read -ra cols <<< "$line"

    # 构建精简 JSON，只保留常用字段
    json_obj=$(jq -n \
        --arg iphone "${cols[0]}" \
        --arg id "${cols[1]}" \
        --arg name "${cols[2]}" \
        --arg address "${cols[6]}" \
        '{id:$id, name:$name, address:$address, iphone:$iphone}')

    # POST 到接口
    curl -s -X PUT -H "Content-Type: application/json" -d "$json_obj" http://127.0.0.1:8000/api/resave

    # 打印调试信息
    echo "Sent: $json_obj"
done <<< "$quota_output"

