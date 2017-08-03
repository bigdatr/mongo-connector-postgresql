Feature: Replicate MongoDB

As my MongoDB collection contains documents
I want to replicate those in PostgreSQL tables
So that my documents are fully replicated

Scenario: Replicate Inserts
    Given I have the environment "replicate_inserts"
    And I run mongo-connector
    And I wait 5 seconds for the replication to be done
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate deletions
    Given I have the environment "replicate_deletions"
    And I run mongo-connector
    And I wait 5 seconds for the replication to be done
    And I delete documents from the collection
    And I wait 5 seconds for the replication to be done
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate updates
    Given I have the environment "replicate_updates"
    And I run mongo-connector
    And I wait 5 seconds for the replication to be done
    And I update the collection
    And I wait 5 seconds for the replication to be done
    When I run the SQL queries
    Then the SQL queries should return the appropriate results
