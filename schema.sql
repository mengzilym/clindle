-- using sqlite;
DROP TABLE IF EXISTS Books;
DROP TABLE IF EXISTS Clips;
CREATE TABLE Books (
    id integer primary key autoincrement,
    title text not null,
    author text,
    cover text
);
CREATE TABLE Clips (
    id integer primary key autoincrement,
    cliptype text not null,
    pos text not null,
    time text not null,
    content text,
    bookid integer,
    FOREIGN KEY(bookid) REFERENCES Books(id)
);
