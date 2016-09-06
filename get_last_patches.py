#! /usr/bin/python
import logging
import re
import sys
import subprocess

FORMAT = '%(asctime)-15s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

LOG = logging.getLogger(__name__)

# lines with repo:
# INTEGRATION_MODULES["$OPENSTACK_GIT_ROOT/openstack-infra/puppet-accessbot"]="origin/master"\n
PARSE_TEMPLATE = "/openstack-infra/"
BRANCH_PATTERN = "(origin/master|[a-f0-9]{40})"


def get_url_for_repo(l):
    'Function for getting url for matched line.'

    repo_path = l.split("\"")[1]
    short_repo_path = repo_path[repo_path.find(PARSE_TEMPLATE):]
    repo_url = ''.join(['https://github.com', short_repo_path, '.git'])
    return repo_url


def get_repos(filename):
    with open(filename, 'r') as f:
        regexp = re.compile(".*%s.*%s.*" % (PARSE_TEMPLATE, BRANCH_PATTERN))
        repos = [get_url_for_repo(f) for f in f.readlines()
                 if regexp.search(f)]
    return repos


def get_last_version(repo_name):
    bash_command = (
        "git ls-remote %s | grep HEAD | awk '{ print $1 }'" % repo_name
    )
    res = subprocess.check_output(bash_command, shell=True)
    if res.endswith('\n'):
        res = res[:-1]

    LOG.info("Got SHA1 %s for %s." % (res, repo_name))
    return res


def set_commits_to_repos(repos_map, filename):
    result_file = '-'.join(['new', filename])

    with open(filename, 'r') as in_file, open(result_file, 'w') as out_file:

        regexp = re.compile(".*%s.*%s.*" % (PARSE_TEMPLATE, BRANCH_PATTERN))
        for line in in_file.readlines():
            if regexp.match(line):
                url = get_url_for_repo(line)

                if url in repos_map:
                    # replace
                    line = re.sub(BRANCH_PATTERN, repos_map[url], line)

                out_file.write(line)
            else:
                # copy original
                out_file.write(line)


def main():
    if len(sys.argv) < 2:
        print "Error: please specify file for parsing."
        return

    repos = get_repos(sys.argv[1])
    repos_with_commit = { r: get_last_version(r) for r in repos}
    set_commits_to_repos(repos_with_commit, sys.argv[1])


if __name__ == '__main__':
    main()
