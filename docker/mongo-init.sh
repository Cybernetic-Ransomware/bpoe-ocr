#!/bin/bash

echo "Waiting 30 seconds for MongoDB components to start..."
sleep 30

echo "Initiating Config Server Replica Set (csrs)..."
mongosh --host mongo-configsv-1:27019 --quiet <<EOF
var cfg = {
  "_id": "csrs",
  "configsvr": true,
  "members": [
    { "_id": 0, "host": "mongo-configsv-1:27019" },
    { "_id": 1, "host": "mongo-configsv-2:27019" },
    { "_id": 2, "host": "mongo-configsv-3:27019" }
  ]
};
try {
  rs.initiate(cfg);
} catch (e) {
  if (e.codeName != 'AlreadyInitialized') {
    printjson(e);
    quit(1);
  }
}
EOF

if [ $? -ne 0 ]; then echo "ERROR: CSRS initiation failed."; exit 1; fi

echo "Initiating Shard 1 Replica Set (rs-shard01)..."
mongosh --host mongo-shrd-01:27018 --quiet <<EOF
var cfg = {
  "_id": "rs-shard01",
  "members": [
    { "_id": 0, "host": "mongo-shrd-01:27018" }
  ]
};
try {
  rs.initiate(cfg);
} catch (e) {
  if (e.codeName != 'AlreadyInitialized') {
    printjson(e);
    quit(1);
  }
}
EOF

if [ $? -ne 0 ]; then echo "ERROR: Shard 1 initiation failed."; exit 1; fi

echo "Initiating Shard 2 Replica Set (rs-shard02)..."
mongosh --host mongo-shrd-02:27018 --quiet <<EOF
var cfg = {
  "_id": "rs-shard02",
  "members": [
    { "_id": 0, "host": "mongo-shrd-02:27018" }
  ]
};
try {
  rs.initiate(cfg);
} catch (e) {
  if (e.codeName != 'AlreadyInitialized') {
    printjson(e);
    quit(1);
  }
}
EOF

if [ $? -ne 0 ]; then echo "ERROR: Shard 2 initiation failed."; exit 1; fi

echo "Waiting 15 seconds for router and replica sets..."
sleep 15

echo "Adding Shards to the Cluster via Router..."
mongosh --host mongo-router-1:27017 --quiet <<EOF
var status = sh.status();
var shard1Exists = false;
var shard2Exists = false;
if (status && status.shards) {
  status.shards.forEach(function(shard) {
    if (shard._id == "rs-shard01") shard1Exists = true;
    if (shard._id == "rs-shard02") shard2Exists = true;
  });
}

if (!shard1Exists) {
  print("Adding shard rs-shard01...");
  var result1 = sh.addShard("rs-shard01/mongo-shrd-01:27018");
  if (!result1.ok) { printjson(result1); quit(1); }
}

if (!shard2Exists) {
  print("Adding shard rs-shard02...");
  var result2 = sh.addShard("rs-shard02/mongo-shrd-02:27018");
  if (!result2.ok) { printjson(result2); quit(1); }
}
EOF

if [ $? -ne 0 ]; then echo "ERROR: Adding shards failed."; exit 1; fi

echo "Cluster Status:"
mongosh --host mongo-router-1:27017 --quiet --eval 'sh.status()'

#Section to enable sharding for a specific DB/Collection
echo "Enabling sharding for database '$MONGO_DB'..."
mongosh --host mongo-router-1:27017 --quiet --eval "sh.enableSharding('$MONGO_DB')"
if [ $? -ne 0 ]; then echo "ERROR: Enabling sharding for $MONGO_DB failed."; exit 1; fi

echo "MongoDB Sharded Cluster initialization script finished."
