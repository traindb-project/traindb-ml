# Parameters for Database Source Definition

Last Update: 11 July 2022

This page describes the parameter specification related to database access of TrainDB-ML, DB source.

---

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [BCP 14](https://tools.ietf.org/html/bcp14) [RFC2119](https://tools.ietf.org/html/rfc2119) [RFC8174](https://tools.ietf.org/html/rfc8174) when, and only when, they appear in all capitals, as shown here.

This document is licensed under [The Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0.html).


Here is a concrete example on how to connect to a MySQL database. (reference: [mindsdb](https://docs.mindsdb.com/sql/create/databases/))
```sql
CREATE DATABASE mysql_datasource
WITH
    engine='mysql',
    parameters={
            "user":"root",
            "port": 3306,
            "password": "Mimzo3i-mxt@9CpThpBj",
            "host": "127.0.0.1",
            "database": "instacart"
    };
```

In the TrainDB-ML perspective, we receive the parameters for database access from the TrainDB main as the following.

```sql
engine='mysql',
parameters={
        "user":"root",
        "port": 3306,
        "password": "Mimzo3i-mxt@9CpThpBj",
        "host": "127.0.0.1",
        "database": "instacart"
};
```
The parameter `engine' have the following values according to legacy DBMS.
* mysql : MySQL database
* postgresql : PostgreSQL database
* kairos: Kairos database (user name equals to database name)
* tibero: Tibero database
* bigquery: Google BigQuery database
* redshift: Amazon Redshift database

### Legacy DBMS access parameters
The following table presents the specification of parameters for legacy DBMS access.

Field Name | Type | Description 
-- | -- | --
engine | String | This fields represents a name of legacy DBMS to access.
user | String |  This fields represents a user ID of legacy DBMS.
password | String |  This fields represents a plain (not encrypted) password for database access.
host | String |  This fields represents a host uri (e.g. IP address) for database access.
port | Integer |  This fields represent a port number for database access.
database | String | This fields represents a name of a database existed in legacy DBMS. In case of Kairos DBMS, a value of this fields equals to a value of `user` field.
ssl | String | **TBD** "enabled" or "disabled"  This fields represents an access mode (SSL/TLS or not) for database connection.
ssl-ca | File | **TBD** This fields represents a certificates for DBMS access security. Secure Socket Layer (SSL) or Transport Layer Security (TLS) from the TrainDB-ML to encrypt a connection to a DB instance running MySQL, PostgreSQL, and so on.

## References

1. [OpenAPI Specification](https://swagger.io/specification/)
2. [CREATE DATABASE Statement](https://docs.mindsdb.com/sql/create/databases/)
