import requests

class GitlabIntegration:
    def __init__(self, token, project_id, gitlab_url):
        self.token = token
        self.project_id = project_id
        self.gitlab_url = gitlab_url

    def create_merge_request(self, source_branch, target_branch="main", title="New Merge Request"):
        url = f"{self.gitlab_url}/api/v4/projects/{self.project_id}/merge_requests"
        headers = {"PRIVATE-TOKEN": self.token}
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title
        }

        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            print(f"Merge request '{title}' created successfully.")
            return response.json()
        else:
            print(f"Failed to create merge request: {response.status_code}")
            print(response.text)
            return None
