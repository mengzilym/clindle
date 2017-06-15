-- using sqlite;
DROP TABLE IF EXISTS Books;
DROP TABLE IF EXISTS Clips;
DROP TABLE IF EXISTS Notes;
DROP TABLE IF EXISTS Marks;

CREATE TABLE Books (
    id integer primary key autoincrement,
    title text not null,
    author text,
    cover text
);
CREATE TABLE Clips (
    id integer primary key autoincrement,
    pos text not null,
    indexpos integer not null,
    time text not null,
    content text,
    bookid integer not null,
    FOREIGN KEY(bookid) REFERENCES Books(id)
);
CREATE TABLE Notes (
    id integer primary key autoincrement,
    pos text not null,
    time text not null,
    content text not null,
    bookid integer not null,
    clipid integer not null,
    FOREIGN KEY(bookid) REFERENCES Books(id),
    FOREIGN KEY(clipid) REFERENCES Clips(id)
);
CREATE TABLE Marks (
    id integer primary key autoincrement,
    pos text not null,
    time text not null,
    bookid integer not null,
    FOREIGN KEY(bookid) REFERENCES Books(id)
);
