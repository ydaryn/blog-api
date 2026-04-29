## Verification (HW4)

### 1. Admin through nginx
```bash
curl -I http://localhost/admin/login/
# Expect: 200 OK, Server: nginx/1.27.0
```

### 2. Static with cache
```bash
curl -I http://localhost/static/admin/css/base.css
# Expect: 200 OK, Cache-Control: public, immutable, Expires: <30 days>
```

### 3. API query
```bash
curl http://localhost/api/posts/
# Expect: JSON post list
```

### 4. Web service not available from outside
```bash
curl http://localhost:8000/
# Expect: Connection refused
```

### 5. 502 if backend failed
```bash
docker compose stop web
curl -I http://localhost/api/posts/
# Expect: 502 Bad Gateway from nginx

docker compose start web  # Run again
```

### 6. WebSocket through nginx
```bash
# Get token
TOKEN=$(curl -X POST http://localhost/api/token/ \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' | jq -r .access)

# Connect to WebSocket (requires wscat: npm install -g wscat)
wscat -c "ws://localhost/ws/posts/<slug>/comments/?token=$TOKEN"

# In another terminal create comment
curl -X POST http://localhost/api/posts/<slug>/comments/ \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"content":"Test via WebSocket"}'

# In wscat terminal you should see notification about new comment
```