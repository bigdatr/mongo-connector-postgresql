Feature: Replicate nested documents

As my MongoDB collection contains nested documents
I want to replicate those in multiple tables with auto-generated primary keys
So that my documents are fully replicated

Scenario: Replicate a document containing a list of documents
    Given I have the environment "replicate_list_of_documents"
    And I run mongo-connector
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate a document containing a list of scalars
    Given I have the environment "replicate_list_of_scalars"
    And I run mongo-connector
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate a document containing a nested list of documents
    Given I have the environment "replicate_list_of_documents_nested"
    And I run mongo-connector
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate a document containing a nested list of scalars
    Given I have the environment "replicate_list_of_scalars_nested"
    And I run mongo-connector
    Then the SQL queries should return the appropriate results

Scenario: Replicate deletions
    Given I have the environment "replicate_deletions"
    And I run mongo-connector
    And I delete the collection
    When I run the SQL queries
    Then the SQL queries should return the appropriate results

Scenario: Replicate updates
    Given I have the environment "replicate_updates"
    And I run mongo-connector
    And I update the collection
    When I run the SQL queries
    Then the SQL queries should return the appropriate results
