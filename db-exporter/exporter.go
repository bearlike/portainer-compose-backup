package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"

	bolt "go.etcd.io/bbolt"
)

type Entry struct {
	Key   string
	Value json.RawMessage
}

func getDataFromBucket(bucketName string, tx *bolt.Tx) ([]Entry, error) {
	b := tx.Bucket([]byte(bucketName))
	if b == nil {
		return nil, fmt.Errorf("bucket not found: %s", bucketName)
	}

	var entries []Entry
	err := b.ForEach(func(k, v []byte) error {
		entries = append(entries, Entry{Key: string(k), Value: v})
		return nil
	})
	if err != nil {
		return nil, err
	}

	return entries, nil
}

func main() {
	// Open the my.db data file in read-only mode
	db, err := bolt.Open("portainer.db", 0600, &bolt.Options{ReadOnly: true})
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	var data = make(map[string][]Entry)
	err = db.View(func(tx *bolt.Tx) error {
		for _, bucket := range []string{"endpoints", "stacks"} {
			entries, err := getDataFromBucket(bucket, tx)
			if err != nil {
				log.Println(err)
				continue
			}

			data[bucket] = entries
		}
		return nil
	})

	// Check for errors
	if err != nil {
		log.Fatal(err)
	}

	file, err := os.Create("/output/portainer_data.json")
	if err != nil {
		log.Fatal(err)
	}

	// Write indented JSON content to file
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	err = encoder.Encode(data)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("JSON data written to data.json")
}