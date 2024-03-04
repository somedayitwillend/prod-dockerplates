items=$(docker ps --format "{{.ID}}" | grep -v somename)
for word in $items
do
    docker stop $word
done
