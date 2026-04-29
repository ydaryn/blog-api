# Blog API - Entity Relationship Diagram

```mermaid
erDiagram
    CustomUser ||--o{ Post        : "creates"
    CustomUser ||--o{ Comment     : "writes"
    Category   ||--o{ Post        : "categorizes"
    Tag        ||--o{ PostTag     : "labeled via"
    Post       ||--o{ PostTag     : "tagged via"
    Post       ||--o{ Comment     : "has"
    Comment    }o--o| Comment     : "replies to"

    CustomUser {
        bigint   id          PK
        string   email       UK  "unique"
        string   first_name
        string   last_name
        string   password
        image    avatar          "nullable"
        boolean  is_active
        boolean  is_staff
        datetime date_joined
        datetime created_at
        datetime updated_at
    }

    Category {
        bigint  id        PK
        string  name      UK  "unique, max_length=100"
        string  slug      UK  "unique, auto from name"
        datetime created_at
        datetime updated_at
    }

    Tag {
        bigint  id        PK
        string  name      UK  "unique, max_length=50"
        string  slug      UK  "unique, auto from name"
        datetime created_at
        datetime updated_at
    }

    PostTag {
        bigint  id       PK
        bigint  post_id  FK
        bigint  tag_id   FK
    }

    Post {
        bigint   id           PK
        bigint   author_id    FK  "CASCADE"
        bigint   category_id  FK  "nullable, SET_NULL"
        string   title            "max_length=200"
        string   slug         UK  "unique, auto from title"
        text     body
        string   status           "draft|published"
        datetime published_at     "nullable"
        datetime created_at
        datetime updated_at
    }

    Comment {
        bigint   id         PK
        bigint   post_id    FK  "CASCADE"
        bigint   author_id  FK  "CASCADE"
        bigint   parent_id  FK  "nullable, self-ref"
        text     body
        datetime created_at
        datetime updated_at
    }
```