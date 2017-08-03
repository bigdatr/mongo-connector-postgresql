Feature: Replicate nested documents

As my MongoDB collection contains nested documents
I want to replicate those in multiple tables with auto-generated primary keys
So that my documents are fully replicated

Scenario: Replicate a document containing a list of documents
    Given I have the environment "replicate_list_of_documents"
    And I run mongo-connector
    And I wait 5 seconds for the replication to be done
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate a document containing a list of scalars
    Given I have the environment "replicate_list_of_scalars"
    And I run mongo-connector
    And I wait 5 seconds for the replication to be done
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate a document containing a nested list of documents
    Given I have the environment "replicate_list_of_documents_nested"
    And I run mongo-connector
    And I wait 5 seconds for the replication to be done
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate a document containing a nested list of scalars
    Given I have the environment "replicate_list_of_scalars_nested"
    And I run mongo-connector
    And I wait 5 seconds for the replication to be done
    When I run the SQL queries
    Then the SQL queries should return the appropriate results
