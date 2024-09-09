# docker build -t bearlike/portainer-db-exporter:latest .
FROM golang:1-alpine
# Adding git to download bbolt package
RUN apk add --no-cache git 
WORKDIR /app
RUN go mod init db-exporter
COPY exporter.go .
# Downloading and installing the bbolt package
RUN go get go.etcd.io/bbolt  
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o exporter .
RUN mkdir /output
RUN touch /app/portainer.db
CMD ["./exporter"]