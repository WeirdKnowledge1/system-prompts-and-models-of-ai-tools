import os
import json
import requests

# --- GitHub API Integration ---

GITHUB_API_BASE_URL = "https://api.github.com"

def _get_github_token():
    """Helper function to retrieve GitHub PAT from environment variable."""
    token = os.getenv("GITHUB_PAT")
    if not token:
        raise ValueError("GITHUB_PAT environment variable not set.")
    return token

def _make_github_request(method, endpoint, token, json_body=None, params=None):
    """
    Helper function to make requests to the GitHub API.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28" # Recommended by GitHub
    }
    url = f"{GITHUB_API_BASE_URL}{endpoint}"

    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=json_body, params=params)
        # Add other methods like PUT, DELETE if needed following the same pattern
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)

        # Some GitHub API calls might return 204 No Content with an empty body
        if response.status_code == 204:
            return None
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        # Attempt to get more details from the response body if possible
        error_details = ""
        try:
            error_details = response.json()
        except json.JSONDecodeError:
            error_details = response.text
        raise Exception(f"GitHub API HTTP error for {method} {url}: {http_err} - Details: {error_details}")
    except requests.exceptions.RequestException as req_err:
        raise Exception(f"GitHub API Request failed for {method} {url}: {req_err}")
    except ValueError as val_err: # For unsupported HTTP method
        raise Exception(f"GitHub API call error: {val_err}")


def github_fetch_repo_metadata(repo_full_name: str):
    """
    Fetches basic repository metadata.
    :param repo_full_name: Full name of the repository (e.g., "owner/repo").
    :return: Dictionary with repository metadata.
    """
    token = _get_github_token()
    endpoint = f"/repos/{repo_full_name}"
    try:
        print(f"Fetching GitHub repo metadata for: {repo_full_name}")
        metadata = _make_github_request("GET", endpoint, token)
        print(f"Successfully fetched metadata for {repo_full_name}")
        return metadata
    except Exception as e:
        print(f"Error fetching GitHub repo metadata for {repo_full_name}: {e}")
        raise


def github_list_files(repo_full_name: str, branch: str = "main", path: str = ""):
    """
    Lists files and folders in a given repository, branch, and path.
    :param repo_full_name: Full name of the repository (e.g., "owner/repo").
    :param branch: Branch name (defaults to "main").
    :param path: Path within the repository (defaults to root).
    :return: List of items (files/directories) in the specified path.
    """
    token = _get_github_token()
    endpoint = f"/repos/{repo_full_name}/contents/{path}"
    params = {"ref": branch}
    try:
        print(f"Listing files for GitHub repo: {repo_full_name}, branch: {branch}, path: '{path}'")
        files_list = _make_github_request("GET", endpoint, token, params=params)
        print(f"Successfully listed files for {repo_full_name}/{path} on branch {branch}")
        return files_list
    except Exception as e:
        print(f"Error listing files for GitHub repo {repo_full_name}: {e}")
        raise


def github_fetch_file_content(repo_full_name: str, file_path: str, branch: str = "main"):
    """
    Fetches the content of a specific file from a repository.
    Note: This function expects the file content to be Base64 encoded by GitHub,
          and it will decode it. For very large files, consider raw media type.
    :param repo_full_name: Full name of the repository (e.g., "owner/repo").
    :param file_path: Path to the file within the repository.
    :param branch: Branch name (defaults to "main").
    :return: Decoded content of the file as a string.
    """
    token = _get_github_token()
    endpoint = f"/repos/{repo_full_name}/contents/{file_path}"
    params = {"ref": branch}
    try:
        print(f"Fetching file content for: {repo_full_name}/{file_path} on branch {branch}")
        file_data = _make_github_request("GET", endpoint, token, params=params)

        if file_data and "content" in file_data and "encoding" in file_data:
            if file_data["encoding"] == "base64":
                import base64
                decoded_content = base64.b64decode(file_data["content"]).decode('utf-8')
                print(f"Successfully fetched and decoded file content for {repo_full_name}/{file_path}")
                return decoded_content
            else:
                raise Exception(f"Unsupported file encoding: {file_data['encoding']}")
        else:
            raise Exception("Invalid file data received from GitHub API or content not found.")

    except Exception as e:
        print(f"Error fetching file content for GitHub repo {repo_full_name}/{file_path}: {e}")
        raise

def github_create_issue(repo_full_name: str, title: str, body: str = ""):
    """
    Creates a new issue in a specified repository.
    :param repo_full_name: Full name of the repository (e.g., "owner/repo").
    :param title: Title of the issue.
    :param body: Body content of the issue (optional).
    :return: Dictionary with the created issue details.
    """
    token = _get_github_token()
    endpoint = f"/repos/{repo_full_name}/issues"
    issue_data = {"title": title}
    if body:
        issue_data["body"] = body

    try:
        print(f"Creating GitHub issue in {repo_full_name} with title: '{title}'")
        created_issue = _make_github_request("POST", endpoint, token, json_body=issue_data)
        print(f"Successfully created issue in {repo_full_name}. Issue ID: {created_issue.get('id')}")
        return created_issue
    except Exception as e:
        print(f"Error creating GitHub issue in {repo_full_name}: {e}")
        raise

# --- HubSpot API Integration ---

HUBSPOT_API_BASE_URL = "https://api.hubapi.com"

def _get_hubspot_token():
    """Helper function to retrieve HubSpot Private App Token from environment variable."""
    token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
    if not token:
        raise ValueError("HUBSPOT_PRIVATE_APP_TOKEN environment variable not set.")
    return token

def _make_hubspot_request(method, endpoint_path, token, json_body=None, params=None):
    """
    Helper function to make requests to the HubSpot API.
    `endpoint_path` should start with a slash, e.g., /crm/v3/objects/contacts
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{HUBSPOT_API_BASE_URL}{endpoint_path}"

    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=json_body, params=params)
        elif method.upper() == 'PATCH': # HubSpot uses PATCH for updates
            response = requests.patch(url, headers=headers, json=json_body, params=params)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, params=params)
        # Add other methods if needed
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        if response.status_code == 204: # For DELETE or successful updates without content
            return None
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        error_details = ""
        try:
            error_details = response.json()
        except json.JSONDecodeError:
            error_details = response.text
        raise Exception(f"HubSpot API HTTP error for {method} {url}: {http_err} - Details: {error_details}")
    except requests.exceptions.RequestException as req_err:
        raise Exception(f"HubSpot API Request failed for {method} {url}: {req_err}")
    except ValueError as val_err:
        raise Exception(f"HubSpot API call error: {val_err}")


def hubspot_create_contact(email: str, firstname: str, lastname: str, **other_properties):
    """
    Creates a new contact in HubSpot.
    :param email: Email of the contact.
    :param firstname: First name of the contact.
    :param lastname: Last name of the contact.
    :param other_properties: Additional HubSpot contact properties as keyword arguments.
    :return: Dictionary with the created contact details.
    """
    token = _get_hubspot_token()
    endpoint_path = "/crm/v3/objects/contacts"
    properties = {
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        **other_properties # Allows adding any other property
    }
    payload = {"properties": properties}

    try:
        print(f"Creating HubSpot contact for email: {email}")
        created_contact = _make_hubspot_request("POST", endpoint_path, token, json_body=payload)
        print(f"Successfully created HubSpot contact for {email}. Contact ID: {created_contact.get('id')}")
        return created_contact
    except Exception as e:
        print(f"Error creating HubSpot contact for {email}: {e}")
        raise

def hubspot_get_contact_by_email(email: str, properties_to_fetch: list = None):
    """
    Retrieves a contact by their email address from HubSpot.
    :param email: Email of the contact to retrieve.
    :param properties_to_fetch: Optional list of property names to fetch.
                                If None, HubSpot default properties are fetched.
    :return: Dictionary with the contact details, or None if not found.
    """
    token = _get_hubspot_token()
    # HubSpot API for searching contacts by email is a bit different.
    # We'll use the search endpoint.
    # Note: This will return the *first* contact found if multiple exist with the same email (shouldn't happen in a clean CRM).
    endpoint_path = "/crm/v3/objects/contacts/search"
    search_payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }
                ]
            }
        ]
    }
    if properties_to_fetch:
        search_payload["properties"] = properties_to_fetch

    try:
        print(f"Fetching HubSpot contact by email: {email}")
        search_results = _make_hubspot_request("POST", endpoint_path, token, json_body=search_payload)
        if search_results and search_results.get("total", 0) > 0:
            contact_data = search_results["results"][0]
            print(f"Successfully fetched HubSpot contact for {email}. Contact ID: {contact_data.get('id')}")
            return contact_data
        else:
            print(f"No HubSpot contact found for email: {email}")
            return None
    except Exception as e:
        print(f"Error fetching HubSpot contact by email {email}: {e}")
        raise


def hubspot_update_contact(contact_id: str, properties_to_update: dict):
    """
    Updates an existing contact's properties in HubSpot.
    :param contact_id: The ID of the contact to update.
    :param properties_to_update: Dictionary of properties to update (e.g., {"phone": "123-456-7890"}).
    :return: Dictionary with the updated contact details.
    """
    if not contact_id:
        raise ValueError("contact_id must be provided to update a HubSpot contact.")
    if not properties_to_update:
        raise ValueError("properties_to_update dictionary cannot be empty.")

    token = _get_hubspot_token()
    endpoint_path = f"/crm/v3/objects/contacts/{contact_id}"
    payload = {"properties": properties_to_update}

    try:
        print(f"Updating HubSpot contact ID: {contact_id} with properties: {properties_to_update}")
        updated_contact = _make_hubspot_request("PATCH", endpoint_path, token, json_body=payload)
        print(f"Successfully updated HubSpot contact ID: {contact_id}")
        return updated_contact
    except Exception as e:
        print(f"Error updating HubSpot contact ID {contact_id}: {e}")
        raise

def hubspot_create_deal(deal_name: str, amount: str, dealstage: str, associated_contact_id: str = None, **other_properties):
    """
    Creates a new deal in HubSpot.
    :param deal_name: Name of the deal.
    :param amount: Amount of the deal (as string or number).
    :param dealstage: The pipeline stage ID for the deal.
    :param associated_contact_id: Optional ID of the contact to associate with this deal.
    :param other_properties: Additional HubSpot deal properties.
    :return: Dictionary with the created deal details.
    """
    token = _get_hubspot_token()
    endpoint_path = "/crm/v3/objects/deals"
    properties = {
        "dealname": deal_name,
        "amount": str(amount), # Ensure amount is a string if API expects it
        "dealstage": dealstage,
        **other_properties
    }
    payload = {"properties": properties}

    if associated_contact_id:
        # Association is done after creation or via a specific associations endpoint for v3+
        # For simplicity in this function, we'll create the deal first,
        # then the caller can use hubspot_associate_deal_to_contact if needed,
        # or one could add association directly if the API supports it in one call for basic cases.
        # The v3 deals API allows setting associations in the create call.
        payload["associations"] = [
            {
                "to": {"id": associated_contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 1}] # 1 = Deal to Contact
            }
        ]
        # Note: The associationTypeId can vary. 1 is typically Deal to Contact.
        # Check HubSpot docs for 'HUBSPOT_DEFINED' association types for Deals.

    try:
        print(f"Creating HubSpot deal: {deal_name}")
        created_deal = _make_hubspot_request("POST", endpoint_path, token, json_body=payload)
        print(f"Successfully created HubSpot deal '{deal_name}'. Deal ID: {created_deal.get('id')}")
        return created_deal
    except Exception as e:
        print(f"Error creating HubSpot deal '{deal_name}': {e}")
        raise


def hubspot_search_company_by_domain(domain_name: str, properties_to_fetch: list = None):
    """
    Searches for a company by its domain name in HubSpot.
    :param domain_name: The domain name to search for (e.g., "example.com").
    :param properties_to_fetch: Optional list of property names to fetch.
    :return: Dictionary with the company details if found, else None.
    """
    token = _get_hubspot_token()
    endpoint_path = "/crm/v3/objects/companies/search"
    search_payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "domain",
                        "operator": "EQ",
                        "value": domain_name
                    }
                ]
            }
        ],
        "limit": 1 # We only expect one company per domain ideally
    }
    if properties_to_fetch:
        search_payload["properties"] = properties_to_fetch

    try:
        print(f"Searching HubSpot company by domain: {domain_name}")
        search_results = _make_hubspot_request("POST", endpoint_path, token, json_body=search_payload)
        if search_results and search_results.get("total", 0) > 0:
            company_data = search_results["results"][0]
            print(f"Successfully found HubSpot company for domain {domain_name}. Company ID: {company_data.get('id')}")
            return company_data
        else:
            print(f"No HubSpot company found for domain: {domain_name}")
            return None
    except Exception as e:
        print(f"Error searching HubSpot company by domain {domain_name}: {e}")
        raise

def hubspot_create_company(company_name: str, domain_name: str = None, **other_properties):
    """
    Creates a new company in HubSpot.
    :param company_name: Name of the company.
    :param domain_name: Optional domain name of the company.
    :param other_properties: Additional HubSpot company properties.
    :return: Dictionary with the created company details.
    """
    token = _get_hubspot_token()
    endpoint_path = "/crm/v3/objects/companies"
    properties = {
        "name": company_name,
        **other_properties
    }
    if domain_name:
        properties["domain"] = domain_name

    payload = {"properties": properties}

    try:
        print(f"Creating HubSpot company: {company_name}")
        created_company = _make_hubspot_request("POST", endpoint_path, token, json_body=payload)
        print(f"Successfully created HubSpot company '{company_name}'. Company ID: {created_company.get('id')}")
        return created_company
    except Exception as e:
        print(f"Error creating HubSpot company '{company_name}': {e}")
        raise

# --- Example Usage (for testing purposes, comment out or remove in production) ---
if __name__ == "__main__":
    print("Starting API Integration examples (ensure environment variables are set)...")

    # --- GitHub Examples ---
    # Note: To run these, you need to set GITHUB_PAT environment variable
    # and use a real public repository you have access to or a test one.
    # Example: export GITHUB_PAT="your_personal_access_token"

    # Test GitHub Repo
    test_github_repo = "octocat/Spoon-Knife" # A common public repo for testing
    # test_github_repo = "YOUR_USERNAME/YOUR_TEST_REPO" # Use your own for create_issue

    print(f"\n--- GitHub API Tests (using repo: {test_github_repo}) ---")
    if os.getenv("GITHUB_PAT"):
        try:
            print("\n1. Fetching repo metadata...")
            metadata = github_fetch_repo_metadata(test_github_repo)
            # print(f"Repo Description: {metadata.get('description')}")
            # print(f"Stars: {metadata.get('stargazers_count')}")

            print("\n2. Listing files at root...")
            files = github_list_files(test_github_repo, path="")
            # for item in files:
            # print(f"  - {item.get('name')} ({item.get('type')})")

            print("\n3. Fetching content of README.md (or another known file)...")
            # Check if README.md exists before fetching
            readme_exists = any(item.get('name', '').lower() == 'readme.md' for item in files if isinstance(item, dict))
            if readme_exists:
                 readme_content = github_fetch_file_content(test_github_repo, "README.md")
                 # print(f"README Content (first 100 chars):\n{readme_content[:100]}...")
            else:
                 print("README.md not found at root, skipping content fetch test for it.")
                 # Try another file if available, e.g. "index.html" if it's a gh-pages repo.
                 # index_html_exists = any(item.get('name', '').lower() == 'index.html' for item in files if isinstance(item, dict))
                 # if index_html_exists:
                 #    print("Attempting to fetch index.html instead...")
                 #    index_content = github_fetch_file_content(test_github_repo, "index.html")
                 #    print(f"index.html Content (first 100 chars):\n{index_content[:100]}...")
                 # else:
                 #    print("No common file like README.md or index.html found for content fetching test.")


            # print("\n4. Creating a test issue (OPTIONAL - ensure repo is suitable for testing)...")
            # Be careful with this on public repos if you don't own them.
            # try:
            #     # Replace "YOUR_USERNAME/YOUR_TEST_REPO_FOR_ISSUES" with a repo you can create issues on
            #     # test_issue_repo = "YOUR_USERNAME/YOUR_TEST_REPO_FOR_ISSUES"
            #     # if test_issue_repo != "YOUR_USERNAME/YOUR_TEST_REPO_FOR_ISSUES": # Ensure it's changed
            #     #    issue_title = f"Test Issue from API Integrations Script {datetime.datetime.now()}"
            #     #    issue_body = "This is a test issue created automatically."
            #     #    created_issue_info = github_create_issue(test_issue_repo, issue_title, issue_body)
            #     #    print(f"Issue created: {created_issue_info.get('html_url')}")
            #     # else:
            #     #    print("Skipping issue creation test as test_issue_repo is not set.")
            #     pass # Commented out by default to prevent accidental issue creation
            # except Exception as e_issue:
            #     print(f"Could not create issue (this is okay if repo is not set up for it): {e_issue}")

        except Exception as e_gh:
            print(f"A GitHub API test failed: {e_gh}")
    else:
        print("GITHUB_PAT not set. Skipping GitHub API tests.")

    # --- HubSpot Examples ---
    # Note: To run these, you need to set HUBSPOT_PRIVATE_APP_TOKEN environment variable
    # and have a HubSpot account (developer or sandbox preferably for testing).
    # Example: export HUBSPOT_PRIVATE_APP_TOKEN="your_private_app_token"

    print(f"\n--- HubSpot API Tests ---")
    if os.getenv("HUBSPOT_PRIVATE_APP_TOKEN"):
        import time # For unique email generation
        timestamp = int(time.time())
        test_email = f"testuser_{timestamp}@example.com"
        test_firstname = "Test"
        test_lastname = f"User{timestamp}"
        updated_phone = f"555-010-{timestamp % 10000:04d}" # Example unique phone

        test_deal_name = f"Test Deal {timestamp}"
        test_deal_amount = str(1000 + timestamp % 500)
        # You'll need a valid deal stage ID from your HubSpot pipeline
        # Find this in HubSpot: Settings -> Objects -> Deals -> Pipelines -> Edit pipeline -> Get internal ID for a stage
        test_deal_stage_id = "DEALSTAGE_ID_PLACEHOLDER" # Replace with a real Deal Stage ID from your portal

        test_company_name = f"TestCo {timestamp} Inc."
        test_company_domain = f"testco{timestamp}.com"

        created_contact_id = None

        try:
            print(f"\n1. Creating HubSpot contact: {test_email}...")
            new_contact = hubspot_create_contact(test_email, test_firstname, test_lastname, phone="111-222-3333")
            created_contact_id = new_contact.get("id")
            # print(f"New contact created with ID: {created_contact_id}")

            if created_contact_id:
                print(f"\n2. Getting HubSpot contact by email: {test_email}...")
                retrieved_contact = hubspot_get_contact_by_email(test_email, properties_to_fetch=["firstname", "lastname", "email", "phone"])
                # print(f"Retrieved contact: {retrieved_contact.get('properties', {}).get('email')}")
                # assert retrieved_contact.get('properties', {}).get('email') == test_email

                print(f"\n3. Updating HubSpot contact ID {created_contact_id} with new phone: {updated_phone}...")
                hubspot_update_contact(created_contact_id, {"phone": updated_phone})
                # Verify update by fetching again
                # updated_retrieved_contact = hubspot_get_contact_by_email(test_email, properties_to_fetch=["phone"])
                # print(f"Updated phone from HubSpot: {updated_retrieved_contact.get('properties', {}).get('phone')}")
                # assert updated_retrieved_contact.get('properties', {}).get('phone') == updated_phone

            # Optional Deal Test
            # if created_contact_id and test_deal_stage_id != "DEALSTAGE_ID_PLACEHOLDER":
            #     print(f"\n4. Creating HubSpot deal '{test_deal_name}' associated with contact {created_contact_id}...")
            #     new_deal = hubspot_create_deal(test_deal_name, test_deal_amount, test_deal_stage_id, associated_contact_id=created_contact_id)
            #     print(f"New deal created with ID: {new_deal.get('id')}")
            # else:
            #     print("\nSkipping deal creation test (contact not created or deal stage ID not set).")

            # Company Tests
            print(f"\n5. Searching for company by domain: {test_company_domain}...")
            existing_company = hubspot_search_company_by_domain(test_company_domain)
            if not existing_company:
                print(f"  Company not found, creating: {test_company_name} with domain {test_company_domain}...")
                new_company = hubspot_create_company(test_company_name, domain_name=test_company_domain, city="Testville")
                # print(f"  New company created with ID: {new_company.get('id')}")
            else:
                print(f"  Company with domain {test_company_domain} already exists: ID {existing_company.get('id')}")

        except Exception as e_hs:
            print(f"A HubSpot API test failed: {e_hs}")
    else:
        print("HUBSPOT_PRIVATE_APP_TOKEN not set. Skipping HubSpot API tests.")

    print("\nAPI Integration examples finished.")

```
