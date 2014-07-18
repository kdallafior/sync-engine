"""Enforce length limit of 255 on Message subjects

Revision ID: 4af5952e8a5b
Revises: 4b4c5579c083
Create Date: 2014-07-18 22:00:45.339930

"""

# revision identifiers, used by Alembic.
revision = '4af5952e8a5b'
down_revision = '4b4c5579c083'

from alembic import op
import sqlalchemy as sa


def truncate_subject(obj):
    if obj.subject is None:
        return
    if len(obj.subject) > 255:
        obj.subject = obj.subject[:255]
    return


def upgrade():
    from inbox.models.session import session_scope
    from inbox.ignition import engine

    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    Base.metadata.reflect(engine)

    class Message(Base):
        __table__ = Base.metadata.tables['message']

    class Thread(Base):
        __table__ = Base.metadata.tables['thread']

    with session_scope(versioned=False, ignore_soft_deletes=False) \
            as db_session:
        count = 0
        for msg in db_session.query(Message).options(
                sa.orm.load_only('subject')).yield_per(500):
            truncate_subject(msg)
            count += 1
            if count > 500:
                db_session.commit()
                count = 0

        for thread in db_session.query(Thread).options(
                sa.orm.load_only('subject')).yield_per(500):
            truncate_subject(thread)
            count += 1
            if count > 500:
                db_session.commit()
                count = 0

    op.alter_column('message', 'subject',
                    type_=sa.String(255), existing_nullable=True)
    op.alter_column('thread', 'subject',
                    type_=sa.String(255), existing_nullable=True)


def downgrade():
    raise Exception("Not supported!")