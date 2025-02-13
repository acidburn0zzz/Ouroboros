from functools import partial

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import MetaData
from ouroboros.utils.meta import id, rename_table, exclude_columns, rename_columns, join_tables

converters = {
    'auth_group': [id()],
    'blogs_category': [id()],
    'commons_material': [id()],
    'django_flatpage': [id()],
    'django_flatpage_sites': [id()],
    'django_site': [id()],
    'profiles_skill': [id()],
    'projects_category': [id()],
    'tagging_tag': [id()],
    'blogs_entry': [id()],

    'auth_user': [join_tables('profiles_profile', 'id', 'user_id'),
                  rename_table('personas_persona'),
                  rename_columns({'icon': 'avator',
                                  'sex': 'gender',
                                  'mood': 'quotes'}),
                  exclude_columns(['pub_state',
                                   'birthday',
                                   'place',
                                   'location',
                                   'url',
                                   'remarks',
                                   'remarks_markup_type',
                                   'user_id',
                                   '_remarks_rendered',
                                   'twitter_token',
                                   'created_at',
                                   'updated_at'])],

    'events_event_members': [rename_table('events_event_attendees'),
                             rename_columns({'user_id': 'persona_id'})],

    'announcements_announcement': [exclude_columns(['updated_by_id',
                                                    'publish_at',
                                                    'publish_at_date']),
                                   rename_columns({'sage': 'silently'})],
    'events_event': [exclude_columns(['publish_at', 'publish_at_date'])],

    'projects_project': [exclude_columns(['updated_by_id',
                                          'publish_at',
                                          'publish_at_date',
                                          'bugwaz_id',
                                          'permission']),
                         rename_columns({'author_id': 'administrator_id'})],

    'projects_project_members': [rename_columns({'user_id': 'persona_id'})],

    'profiles_profile_skills': [rename_columns({'user_id': 'persona_id'})],

    'star_star': [rename_table('stars_star'),
                  rename_columns({'comment': 'quotes'}),
                  exclude_columns(['tag'])]
}

def pipe_converters(tables, src_tn, key):
    def piped(x):
        r = x
        for o in converters[src_tn]:
            d = o(tables, src_tn)
            r = d[key](r)
        return r

    return piped


if __name__ == '__main__':

    src_engine = create_engine('sqlite:///db/kawaz.db')
    dst_engine = create_engine('sqlite:///db/kawaz3.db', echo=True)

    src_meta = MetaData(bind=src_engine)
    src_meta.reflect()
    dst_meta = MetaData(bind=dst_engine)

    src_session = sessionmaker(bind=src_engine)()
    dst_session = sessionmaker(bind=dst_engine)()

    src_tables = src_meta.tables

    for src_tn in src_tables:
        if src_tn in converters:
            converter = partial(pipe_converters, src_tables, src_tn)
            get_query = converter('query')
            convert_table = converter('table')
            convert_record = converter('record')

            src_table = src_tables[src_tn]
            dst_table = convert_table(src_table).tometadata(dst_meta)
            dst_table.create()

            src_query = get_query(src_table).select()

            for r in src_session.query(src_query).all():
                src_record = r._asdict()
                dst_record = convert_record(src_record)
                ins = dst_table.insert(values=dst_record)
                dst_session.execute(ins)
            dst_session.commit()
