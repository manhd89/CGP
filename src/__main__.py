import re
from src import info, error, silent_error, utils, domains, cloudflare, PREFIX, MAX_LISTS, MAX_LIST_SIZE

class CloudflareManager:
    def __init__(self, prefix, max_lists, max_list_size):
        self.prefix = prefix
        self.max_lists = max_lists
        self.max_list_size = max_list_size
        self.adlist_name = f"[{self.prefix}]"
        self.policy_name = f"[{self.prefix}] Block Ads"

    def run(self):
        converter = domains.DomainConverter()
        domain_list = converter.process_urls()
        total_lines = len(domain_list)

        if total_lines == 0:
            silent_error("No domain")
            return

        if total_lines > self.max_list_size * self.max_lists:
            error(f"The domains list has more than {self.max_list_size * self.max_lists} lines")
            return

        total_lists = -(-total_lines // self.max_list_size)  # Ceiling division
        current_lists = cloudflare.get_current_lists()["result"] or []
        current_policies = cloudflare.get_current_policies()["result"] or []

        info(f"Total lists on Cloudflare: {len(current_lists)}")
        total_domains = sum([l['count'] for l in current_lists]) if current_lists else 0
        info(f"Total domains on Cloudflare: {total_domains}")

        current_lists_with_prefix = [
            list_item for list_item in current_lists if self.prefix in list_item["name"]
        ]
        current_lists_count = len(current_lists_with_prefix)
        current_lists_count_without_prefix = len(current_lists) - current_lists_count

        if total_lines == sum([l['count'] for l in current_lists_with_prefix]):
            silent_error("Same size, skipping")
            return

        if total_lists > self.max_lists - current_lists_count_without_prefix:
            error(
                f"The number of lists required ({total_lists}) is greater than the maximum allowed "
                f"({self.max_lists - current_lists_count_without_prefix})"
            )
            return

        chunked_lists = utils.split_domain_list(domain_list)
        info(f"Total chunked lists generated: {len(chunked_lists)}")

        used_list_ids = []
        excess_list_ids = []
        existing_indices = [
            int(re.search(r'\d+', list_item["name"]).group())
            for list_item in current_lists_with_prefix
            if f"{self.adlist_name}" in list_item["name"]
        ]
        total_lists = len(chunked_lists)
        missing_indices = utils.get_missing_indices(existing_indices, total_lists)

        for index in range(1, total_lists + 1):
            formatted_counter = f"{index:03d}"
            info(f"Creating list {self.adlist_name} - {formatted_counter}")

            if index in missing_indices and index - 1 < len(chunked_lists):
                payload = utils.create_list_payload(
                    f"{self.adlist_name} - {formatted_counter}", chunked_lists[index - 1]
                )
            else:
                payload = utils.create_list_payload(
                    f"{self.adlist_name} - {formatted_counter}", []
                )

            created_list = cloudflare.create_list(payload)
            if created_list:
                used_list_ids.append(created_list.get("result", {}).get("id"))

        json_data = utils.create_policy_json(
            self.policy_name, used_list_ids
        )

        policy_id = None
        for policy_item in current_policies:
            if policy_item["name"] == self.policy_name:
                policy_id = policy_item["id"]
                break

        if not policy_id or policy_id == "null":
            info(f"Creating policy {self.policy_name}")
            cloudflare.create_policy(json_data)
        else:
            info(f"Updating policy {self.policy_name}")
            cloudflare.update_policy(policy_id, json_data)

        for list_item in current_lists:
            if f"{self.adlist_name}" in list_item["name"] and list_item["id"] not in used_list_ids:
                excess_list_ids.append(list_item["id"])

        if excess_list_ids:
            for list_id in excess_list_ids:
                info(f"Deleting list {list_id}")
                cloudflare.delete_list(list_id)

    def leave(self):
        current_lists = cloudflare.get_current_lists()["result"] or []
        current_policies = cloudflare.get_current_policies()["result"] or []
        policy_id = None
        list_ids_to_delete = []

        for policy_item in current_policies:
            if policy_item["name"] == self.policy_name:
                policy_id = policy_item["id"]
                break

        if policy_id:
            info(f"Deleting policy {self.policy_name}")
            cloudflare.delete_policy(policy_id)

        for list_item in current_lists:
            if f"{self.adlist_name}" in list_item["name"]:
                list_ids_to_delete.append(list_item['id'])

        for list_id in list_ids_to_delete:
            info(f"Deleting list {list_id}")
            cloudflare.delete_list(list_id)

if __name__ == "__main__":
    cloudflare_manager = CloudflareManager(PREFIX, MAX_LISTS, MAX_LIST_SIZE)
    cloudflare_manager.run()
    # cloudflare_manager.leave() # Uncomment if you want to leave script
