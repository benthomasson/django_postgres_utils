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


def model_pk_seq(model, n):
    if n <= 0:
        return xrange(0)
    cursor = connection.cursor()
    cursor.execute("select multi_nextval(%s, %s)", (model._meta.pk_sequence, n))
    result = cursor.fetchone()[0]
    assert result > 0, "multi_nextval returned a negative pk value for {0}, {1}: {2}".format(model, n, result)
    assert result + n > 0, "multi_nextval returned a negative pk range for {0}, {1}: {2} to {3}".format(model, n, result, result + n)
    return xrange(result, result + n)
