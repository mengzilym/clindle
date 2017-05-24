-- using sqlite;
drop table if exists Books;
drop table if exists Clips;
create table Books (
    id int not null primary key autoincrement,
    title text not null
);
create table Clips (
    id int not null primary key autoincrement,
    clip_type char not null,
    pos char not null,
    time char not null,
    content text not null,
    book_id int
)
