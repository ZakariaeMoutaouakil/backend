import os

import dotenv
from neo4j import GraphDatabase

# Create your models here.

dotenv.load_dotenv("/etc/secrets/Neo4j-1b4d038b-Created-2024-01-09.txt")

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

driver = GraphDatabase.driver(URI, auth=AUTH)

secret = "sdhSDGDS4763dfgdjg@DFGGF"
