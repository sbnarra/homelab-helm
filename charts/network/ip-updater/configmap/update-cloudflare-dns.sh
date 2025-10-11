#!/bin/sh

set -e
# CLOUDFLARE_API_KEY="xxx"
# CLOUDFLARE_EMAIL="xxx@gmail.com"
# DOMAIN=xxx.com

apk add --no-cache jq curl

DNS_IP_FILE=/ip/cloudflare-ip.txt
CACHE=/ip/dynamic-ip.cache

cloudflare() {
  echo curl -H \"X-Auth-Email: $CLOUDFLARE_EMAIL\" -H \"X-Auth-Key: $CLOUDFLARE_API_KEY\" -H \"Content-Type: application/json\" https://api.cloudflare.com/client/v4/$@
  curl -H "X-Auth-Email: $CLOUDFLARE_EMAIL" -H "X-Auth-Key: $CLOUDFLARE_API_KEY" -H "Content-Type: application/json" "https://api.cloudflare.com/client/v4/$@"
}

update_dns() {
  public_ip=$(curl 'https://api.ipify.org?format=json' -s | jq -r '.ip')
  if [ "$public_ip" = "$dns_ip" ]; then
    echo "No IP Change: $dns_ip"
    exit 0
  fi

  echo "Updating IP: $dns_ip -> $public_ip"
  cloudflare "zones/$zone_id/dns_records/$record_id" -X PUT --data '{"type":"A","name":"@","content":"'$public_ip'", "ttl": 600}'
  dns_ip=$public_ip
  write_cache

  echo "Updated Cloudflare: $dns_ip"
}

write_cache() {
  cat <<EOF | tee $CACHE || true
zone_id=$zone_id
record_id=$record_id
dns_ip=$dns_ip
EOF
}

### Script Start
if [ -e $CACHE ]; then
  echo "Cached IP Exists"
  . $CACHE
  update_dns
else
  echo "No Cached IP"

  echo "Getting Zone ID"
  cloudflare "zones" -o /tmp/zones.json
  zone_id=$(jq -r ".result[] | select(.name == \"$DOMAIN\").id" /tmp/zones.json)
  if [ "$zone_id" = "" ]; then
    echo "No Zone for $DOMAIN"
    exit 0
  fi
  echo "Zone ID: $zone_id"

  echo "Getting DNS Records"
  cloudflare "zones/$zone_id/dns_records" -o /tmp/records.json

  echo "Finding $DOMAIN DNS Entry"
  record_id=$(jq -r ".result[] | select(.zone_name == \"$DOMAIN\" and .type == \"A\").id" /tmp/records.json)
  if [ "$record_id" = "" ]; then
    echo "No DNS Record to update for $DOMAIN"
    exit 0
  fi
  echo "DNS Record ID: $record_id"

  dns_ip=$(jq -r ".result[] | select(.zone_name == \"$DOMAIN\" and .type == \"A\").content" /tmp/records.json)
  echo "Current DNS IP: $dns_ip"

  write_cache
  . $CACHE
  update_dns
fi
