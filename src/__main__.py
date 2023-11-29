import re
from src import (
    error,
    utils,
    domains,
    cloudflare,
    silent_error,
    PREFIX,
    MAX_LISTS,
    MAX_LIST_SIZE,
)

class CloudflareManager: 
    def __init__(self, prefix, max_lists, max_list_size):
        self.prefix = prefix
        self.max_lists = max_lists
        self.max_list_size = max_list_size

    def run(self):
        converter = domains.DomainConverter()
        domain_list = converter.process_urls()
        total_lines = len(domain_list)
        if total_lines > self.max_list_size * self.max_lists:
            error(f"The domains list has more than {self.max_list_size * self.max_lists} lines")
        total_lists = total_lines // self.max_list_size
        if total_lines % self.max_list_size != 0:
            total_lists += 1
        current_lists = cloudflare.get_current_lists()
        current_policies = cloudflare.get_current_policies()
        current_lists_count = 0
        current_lists_count_without_prefix = 0
        if current_lists.get("result"):
            current_lists["result"].sort(key=lambda x: int(re.search(r'\d+', x["name"]).group()))
            current_lists_count = len(
                [list_item for list_item in current_lists["result"] if self.prefix in list_item["name"]]
            )
            current_lists_count_without_prefix = len(
                [list_item for list_item in current_lists["result"] if self.prefix not in list_item["name"]]
            )
            if total_lines == sum([l["count"] for l in current_lists["result"]]):
                silent_error("Same size, skipping")
        if total_lists > self.max_lists - current_lists_count_without_prefix:
            error(
                f"The number of lists required ({total_lists}) is greater than the maximum allowed "
                f"({self.max_lists - current_lists_count_without_prefix})"
            )
        chunked_lists = utils.split_domain_list(domain_list) 
        used_list_ids = []
        excess_list_ids = []
        if current_lists_count > 0:
            used_list_ids, excess_list_ids = utils.update_lists(current_lists, chunked_lists)
        used_list_ids += utils.create_lists(chunked_lists, current_lists_count)
        utils.update_or_create_policy(current_policies, used_list_ids)
        if excess_list_ids:
            utils.delete_excess_lists(current_lists, excess_list_ids)

    def leave(self):
        current_lists = cloudflare.get_current_lists()
        current_policies = cloudflare.get_current_policies()
        utils.delete_policy(current_policies)
        utils.delete_lists(current_lists)
         
if __name__ == "__main__":
    cloudflare_manager = CloudflareManager(PREFIX, MAX_LISTS, MAX_LIST_SIZE)
    cloudflare_manager.run()   
    # cloudflare_manager.leave()
