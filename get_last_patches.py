#! /usr/bin/python
import re
import sys
import subprocess

# lines with repo:
# INTEGRATION_MODULES["$OPENSTACK_GIT_ROOT/openstack-infra/puppet-accessbot"]="origin/master"\n
parse_template = "/openstack-infra/"
def get_url_for_repo(l):
    'Function for getting url for matched line.'

    repo_path = l.split("\"")[1]
    short_repo_path = repo_path[repo_path.find(parse_template):]
    repo_url = ''.join(['https://github.com', short_repo_path, '.git'])
    return repo_url


def get_repos(filename):
    with open(filename, 'r') as f:
        regexp = re.compile(".*%s.*master.*" % parse_template)
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
    return res


def set_commits_to_repos(repos_map, filename):
    result_file = '-'.join(['new', filename])

    with open(filename, 'r') as in_file, open(result_file, 'w') as out_file:
        regexp = re.compile(".*%s.*master.*" % parse_template)
        for line in in_file.readlines():
            if regexp.match(line):
                # replace
                url = get_url_for_repo(line)
                line = line.replace('origin/master', repos_map[url])
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


main()
