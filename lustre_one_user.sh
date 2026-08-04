#!/bin/bash
set -e

name="$1"
address="$2"
CLUSTER_ID=9654

if [[ -z "$name" || -z "$address" ]]; then
  echo "Usage: $0 <username> <lustre_path>"
  exit 1
fi

# 获取 uid
id=$(id -u "$name" 2>/dev/null || echo 0)

# 只取最后一行（真正的数据行）
line=$(lfs quota -uh "$name" "$address" | tail -n 1)

[[ -z "$line" ]] && {
  echo "No quota info found"
  exit 1
}

# 拆列
read -ra cols <<< "$line"

filesystem="${cols[0]}"
used="${cols[1]}"
quota="${cols[2]}"

# 构建 JSON
json_obj=$(jq -n \
  --argjson id "$id" \
  --arg name "$name" \
  --arg address "$filesystem" \
  --arg num "$used" \
  --arg iphone "$quota" \
  --arg cluster_id "$CLUSTER_ID" \
  '{
    id: $id,
    name: $name,
    address: $address,
    num: $num,
    iphone: $iphone,
    cluster_id: $cluster_id
  }'
)

# PUT 到接口
response=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
  -H "Content-Type: application/json" \
  -d "$json_obj" \
  http://10.82.4.120:8000/api/resave)

echo "Sent: $json_obj | HTTP: $response"
