import sqlite3
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB = 'social_network.db'

driver = GraphDatabase.driver(
    os.environ.get('NEO4J_URI'),
    auth=(
        os.environ.get('NEO4J_USERNAME'),
        os.environ.get('NEO4J_PASSWORD')
    )
)

def migrate(users, posts, followers):
    with driver.session() as session:
        # Users
        for user in users:
            session.run(
                'MERGE (u:User {id: $id}) SET u.username = $username, u.name = $name',
                id=user['id'], username=user['username'], name=user['name']
            )
        print(f"Migrated {len(users)} users")

        # Posts + POSTED relationships
        for post in posts:
            session.run(
                '''
                MATCH (u:User {id: $user_id})
                MERGE (p:Post {id: $id})
                SET p.content = $content, p.timestamp = $timestamp
                MERGE (u)-[:POSTED]->(p)
                ''',
                id=post['id'], user_id=post['user_id'],
                content=post['content'], timestamp=post['timestamp']
            )
        print(f"Migrated {len(posts)} posts")

        # FOLLOWS relationships
        for follow in followers:
            session.run(
                '''
                MATCH (a:User {id: $follower_id}), (b:User {id: $followee_id})
                MERGE (a)-[:FOLLOWS]->(b)
                ''',
                follower_id=follow['follower_id'], followee_id=follow['followee_id']
            )
        print(f"Migrated {len(followers)} follow relationships")

def read_sqlite():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT id, username, name FROM users')
    users = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT id, user_id, content, timestamp FROM posts')
    posts = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT follower_id, followee_id FROM followers')
    followers = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return users, posts, followers


if __name__ == '__main__':
    print("Reading data from SQLite...")
    users, posts, followers = read_sqlite()
    print("Inserting into Neo4j...")
    migrate(users, posts, followers)
    print("Migration complete")
    driver.close()