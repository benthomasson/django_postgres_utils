from __future__ import print_function
from django.db import connection


def make_materialized_view(name, unique_index, qs):
    raw_query, params = qs.query.sql_with_params()
    params = tuple([("'%s'" % unicode(p).replace('%', '%%')) if isinstance(p, basestring) else str(p) for p in params])
    raw_query = raw_query.replace('%s', '{}').format(*params).replace('%', '%%')
    sql = ('DROP MATERIALIZED VIEW IF EXISTS {0} CASCADE;\n'.format(name) +
           'CREATE MATERIALIZED VIEW {0} AS\n'.format(name) +
           raw_query + ";\n" +
           'create unique index "{0}_unique" on "{0}" ("{1}");'.format(name, unique_index))
    return sql


def make_materialized_view_non_unique(name, qs):
    raw_query, params = qs.query.sql_with_params()
    params = tuple([("'%s'" % unicode(p).replace('%', '%%')) if isinstance(p, basestring) else str(p) for p in params])
    raw_query = raw_query.replace('%s', '{}').format(*params).replace('%', '%%')
    sql = ('DROP MATERIALIZED VIEW IF EXISTS {0} CASCADE;\n'.format(name) +
           'CREATE MATERIALIZED VIEW {0} AS\n'.format(name) +
           raw_query + ";")
    return sql


multi_nextval = '''
CREATE OR REPLACE FUNCTION multi_nextval(use_seqname TEXT, use_increment INT4) RETURNS INT4 AS $$

DECLARE

    reply int4;

BEGIN

    perform pg_advisory_lock(123);

    execute 'ALTER SEQUENCE ' || quote_ident(use_seqname) || ' INCREMENT BY ' || use_increment::text;

    reply := nextval(use_seqname);

    execute 'ALTER SEQUENCE ' || quote_ident(use_seqname) || ' INCREMENT BY 1';

    perform pg_advisory_unlock(123);

    return reply;

END;

$$ LANGUAGE 'plpgsql';
'''


def install_multi_nextval():
    cursor = connection.cursor()
    cursor.execute(multi_nextval)


def model_pk_seq(model, n):
    if not hasattr(model._meta):
        raise AttributeError("pk_sequence is required on {0}._meta".format(model))
    if n <= 0:
        return xrange(0)
    cursor = connection.cursor()
    cursor.execute("select multi_nextval(%s, %s)", (model._meta.pk_sequence, n))
    result = cursor.fetchone()[0]
    assert result > 0, "multi_nextval returned a negative pk value for {0}, {1}: {2}".format(model, n, result)
    assert result - n + 1 > 0, "multi_nextval returned a negative pk range for {0}, {1}: {2} to {3}".format(model, result - n + 1,  result + 1)
    return xrange(result - n + 1, result + 1)
