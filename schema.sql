drop table if exists files_info;
create table files_info (
  id integer primary key autoincrement,
  md5 string not null,
  title string not null,
  url string not null
);