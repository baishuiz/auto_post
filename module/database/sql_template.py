get_user_password_sql = '''
select
    username, password, usertype
from
    auto_post_users
where
    username = '{username}' and deleted = 0
'''

insert_user_sql = '''
insert into
    auto_post_users
    (`username`, `password`, `usertype`, `name`)
values
    ('{username}', '{password}', {usertype}, '{name}')
'''

update_user_sql = '''
update
    auto_post_users
set
    password = '{password}', usertype = {usertype},
    name = '{name}'
where
    username = '{username}'
'''

insert_house_info_sql = '''
insert into
    auto_post_house_info
    (`sheet`, `idx`, `community`, `floor`, `total_floor`,
     `addr`, `area`, `price`, `title`)
values
    ('%s', %s, '%s', %s, %s, '%s', %s, %s, '%s')
'''