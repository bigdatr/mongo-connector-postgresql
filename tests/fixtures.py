# -*- coding: utf-8 -*-

TEST_SQL_BULK_INSERT_1 = ' '.join(
    [
        line.strip(' ')
        for line in """
            WITH col_data_0 (_creationDate, field1, field2_subfield) AS
                (VALUES (NULL::TIMESTAMP, 'val'::TEXT, NULL::TEXT))
            INSERT INTO col (_creationDate, field1, field2_subfield)
            SELECT
                col_data_0._creationDate AS _creationDate,
                col_data_0.field1 AS field1,
                col_data_0.field2_subfield AS field2_subfield
            FROM col_data_0
        """.splitlines()
        if line.strip(' ')
    ]
)

TEST_SQL_BULK_INSERT_2 = ' '.join(
    [
        line.strip(' ')
        for line in """
            WITH col_data_0 (_creationDate, field1, field2_subfield) AS
                (VALUES (NULL::TIMESTAMP, 'val1'::TEXT, 'val2'::TEXT))
            INSERT INTO col (_creationDate, field1, field2_subfield)
            SELECT
                col_data_0._creationDate AS _creationDate,
                col_data_0.field1 AS field1,
                col_data_0.field2_subfield AS field2_subfield
            FROM col_data_0
        """.splitlines()
        if line.strip(' ')
    ]
)

TEST_SQL_BULK_INSERT_ARRAY_1 = ' '.join(
    [
        line.strip(' ')
        for line in """
            WITH
                col1_data_0 (_creationDate) AS
                    (VALUES (NULL::TIMESTAMP)),
                col1_rows_0 AS
                    (INSERT INTO col1 (_creationDate)
                    SELECT
                        col1_data_0._creationDate AS _creationDate
                    FROM col1_data_0
                    RETURNING _id),
                col_array_data_1 (_creationDate, field1, id_col1) AS
                    (VALUES (NULL::TIMESTAMP, 'val'::TEXT, 1::INT)),
                col_array_rows_1 AS
                    (INSERT INTO col_array (_creationDate, field1, id_col1)
                    SELECT
                        col_array_data_1._creationDate AS _creationDate,
                        col_array_data_1.field1 AS field1,
                        col_array_data_1.id_col1 AS id_col1
                    FROM
                        col_array_data_1,
                        col1_rows_0
                    RETURNING _id),
                col_scalar_data_2 (_creationDate, id_col1, scalar) AS
                    (VALUES (NULL::TIMESTAMP, 1::INT, 1::INT)),
                col_scalar_rows_2 AS
                    (INSERT INTO col_scalar (_creationDate, id_col1, scalar)
                    SELECT
                        col_scalar_data_2._creationDate AS _creationDate,
                        col_scalar_data_2.id_col1 AS id_col1,
                        col_scalar_data_2.scalar AS scalar
                    FROM
                        col_scalar_data_2,
                        col1_rows_0
                    RETURNING _id),
                col_scalar_data_3 (_creationDate, id_col1, scalar) AS
                    (VALUES (NULL::TIMESTAMP, 1::INT, 2::INT)),
                col_scalar_rows_3 AS
                    (INSERT INTO col_scalar (_creationDate, id_col1, scalar)
                    SELECT
                        col_scalar_data_3._creationDate AS _creationDate,
                        col_scalar_data_3.id_col1 AS id_col1,
                        col_scalar_data_3.scalar AS scalar
                    FROM
                        col_scalar_data_3,
                        col1_rows_0
                    RETURNING _id),
                col_scalar_data_4 (_creationDate, id_col1, scalar) AS
                    (VALUES (NULL::TIMESTAMP, 1::INT, 3::INT))
            INSERT INTO col_scalar (_creationDate, id_col1, scalar)
            SELECT
                col_scalar_data_4._creationDate AS _creationDate,
                col_scalar_data_4.id_col1 AS id_col1,
                col_scalar_data_4.scalar AS scalar
            FROM
                col_scalar_data_4,
                col1_rows_0
        """.splitlines()
        if line.strip(' ')
    ]
)

TEST_SQL_BULK_INSERT_ARRAY_2 = ' '.join([
    line.strip(' ')
    for line in """
        WITH col1_data_0 (_creationDate) AS
            (VALUES (NULL::TIMESTAMP))
        INSERT INTO col1 (_creationDate)
        SELECT
            col1_data_0._creationDate AS _creationDate
        FROM col1_data_0
    """.splitlines()
    if line.strip(' ')
])

TEST_PGMAN_UPDATE = ' '.join([
    line.strip(' ')
    for line in """
        WITH
            col_data_0 (_creationDate, _id, field1) AS
                (VALUES (NULL::TIMESTAMP, 1::INT, 'val1'::TEXT)),
            col_rows_0 AS
                (INSERT INTO col (_creationDate, _id, field1)
                SELECT
                    col_data_0._creationDate AS _creationDate,
                    col_data_0._id AS _id,
                    col_data_0.field1 AS field1
                FROM col_data_0
                RETURNING _id),
            col_field2_data_1 (_creationDate, _id, id_col, subfield1) AS
                (VALUES (NULL::TIMESTAMP, NULL::INT, 1::INT, 'subval1'::TEXT))
        INSERT INTO col_field2 (_creationDate, _id, id_col, subfield1)
        SELECT
            col_field2_data_1._creationDate AS _creationDate,
            col_field2_data_1._id AS _id,
            col_field2_data_1.id_col AS id_col,
            col_field2_data_1.subfield1 AS subfield1
        FROM
            col_field2_data_1,
            col_rows_0
    """.splitlines()
    if line.strip(' ')
])

TEST_PGMAN_BULK_UPSERT_1 = ' '.join([
    line.strip(' ')
    for line in """
        WITH
            col_data_0 (_creationDate, _id, field1) AS
                (VALUES (NULL::TIMESTAMP, 1::INT, 'val1'::TEXT)),
            col_rows_0 AS
                (INSERT INTO col (_creationDate, _id, field1)
                SELECT
                    col_data_0._creationDate AS _creationDate,
                    col_data_0._id AS _id,
                    col_data_0.field1 AS field1
                FROM col_data_0
                RETURNING _id),
            col_field2_data_1 (_creationDate, _id, id_col, subfield1) AS
                (VALUES (NULL::TIMESTAMP, NULL::INT, 1::INT, 'subval1'::TEXT))
        INSERT INTO col_field2 (_creationDate, _id, id_col, subfield1)
        SELECT
            col_field2_data_1._creationDate AS _creationDate,
            col_field2_data_1._id AS _id,
            col_field2_data_1.id_col AS id_col,
            col_field2_data_1.subfield1 AS subfield1
        FROM
            col_field2_data_1,
            col_rows_0
    """.splitlines()
    if line.strip(' ')
])

TEST_PGMAN_BULK_UPSERT_2 = ' '.join([
    line.strip(' ')
    for line in """
        WITH
            col_data_0 (_creationDate, _id, field1) AS
                (VALUES (NULL::TIMESTAMP, 2::INT, 'val2'::TEXT)),
            col_rows_0 AS
                (INSERT INTO col (_creationDate, _id, field1)
                SELECT
                    col_data_0._creationDate AS _creationDate,
                    col_data_0._id AS _id,
                    col_data_0.field1 AS field1
                FROM col_data_0
                RETURNING _id),
            col_field2_data_1 (_creationDate, _id, id_col, subfield1) AS
                (VALUES (NULL::TIMESTAMP, NULL::INT, 2::INT, 'subval2'::TEXT))
        INSERT INTO col_field2 (_creationDate, _id, id_col, subfield1)
        SELECT
            col_field2_data_1._creationDate AS _creationDate,
            col_field2_data_1._id AS _id,
            col_field2_data_1.id_col AS id_col,
            col_field2_data_1.subfield1 AS subfield1
        FROM
            col_field2_data_1,
            col_rows_0
    """.splitlines()
    if line.strip(' ')
])

TEST_PGMAN_BULK_UPSERT_3 = ' '.join([
    line.strip(' ')
    for line in """
        WITH
            col_data_0 (_creationDate, _id, field1) AS
                (VALUES (NULL::TIMESTAMP, 3::INT, 'val3'::TEXT)),
            col_rows_0 AS
                (INSERT INTO col (_creationDate, _id, field1)
                SELECT
                    col_data_0._creationDate AS _creationDate,
                    col_data_0._id AS _id,
                    col_data_0.field1 AS field1
                FROM col_data_0
                RETURNING _id),
            col_field2_data_1 (_creationDate, _id, id_col, subfield1) AS
                (VALUES (NULL::TIMESTAMP, NULL::INT, 3::INT, 'subval3'::TEXT))
        INSERT INTO col_field2 (_creationDate, _id, id_col, subfield1)
        SELECT
            col_field2_data_1._creationDate AS _creationDate,
            col_field2_data_1._id AS _id,
            col_field2_data_1.id_col AS id_col,
            col_field2_data_1.subfield1 AS subfield1
        FROM
            col_field2_data_1,
            col_rows_0
    """.splitlines()
    if line.strip(' ')
])

TEST_PGMAN_UPSERT = ' '.join([
    line.strip(' ')
    for line in """
        WITH
            col_data_0 (_creationDate, _id, field1) AS
                (VALUES (NULL::TIMESTAMP, 1::INT, 'val1'::TEXT)),
            col_rows_0 AS
                (INSERT INTO col (_creationDate, _id, field1)
                SELECT
                    col_data_0._creationDate AS _creationDate,
                    col_data_0._id AS _id,
                    col_data_0.field1 AS field1
                FROM col_data_0
                RETURNING _id),
            col_field2_data_1 (_creationDate, _id, id_col, subfield1) AS
                (VALUES (NULL::TIMESTAMP, NULL::INT, 1::INT, 'subval1'::TEXT))
        INSERT INTO col_field2 (_creationDate, _id, id_col, subfield1)
        SELECT
            col_field2_data_1._creationDate AS _creationDate,
            col_field2_data_1._id AS _id,
            col_field2_data_1.id_col AS id_col,
            col_field2_data_1.subfield1 AS subfield1
        FROM
            col_field2_data_1,
            col_rows_0
    """.splitlines()
    if line.strip(' ')
])
