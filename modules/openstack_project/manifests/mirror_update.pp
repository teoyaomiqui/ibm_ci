# == Class: openstack_project::mirror_update
#
class openstack_project::mirror_update (
  $sysadmins = [],
  $bandersnatch_keytab = '',
  $reprepro_keytab = '',
  $admin_keytab = '',
) {

  class { 'openstack_project::server':
    sysadmins => $sysadmins,
    afs       => true,
  }

  class { 'bandersnatch':
    bandersnatch_source => 'https://bitbucket.org/jeblair/bandersnatch',
  }

  class { 'bandersnatch::mirror':
    mirror_root => '/afs/.openstack.org/mirror/pypi',
    static_root => '/afs/.openstack.org/mirror',
    hash_index  => true,
    require     => Class['bandersnatch'],
  }

  file { '/etc/bandersnatch.keytab':
    owner   => 'root',
    group   => 'root',
    mode    => '0400',
    content => $bandersnatch_keytab,
  }

  file { '/etc/afsadmin.keytab':
    owner   => 'root',
    group   => 'root',
    mode    => '0400',
    content => $admin_keytab,
  }

  file { '/usr/local/bin/bandersnatch-mirror-update':
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0755',
    source  => 'puppet:///modules/openstack_project/bandersnatch-mirror-update.sh',
  }

  cron { 'bandersnatch':
    user        => $user,
    minute      => '*/5',
    command     => 'flock -n /var/run/bandersnatch/mirror.lock bandersnatch-mirror-update >>/var/log/bandersnatch/mirror.log 2>&1',
    environment => 'PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
    require     => [
       File['/usr/local/bin/bandersnatch-mirror-update'],
       File['/etc/afsadmin.keytab'],
       File['/etc/bandersnatch.keytab'],
       Class['bandersnatch::mirror']
    ]
  }

  # TODO(clarkb) this setup needs to go in a class of its own. It is not
  # in the define because it is common to all reprepro mirrors.
  package { 'reprepro':
    ensure => present,
  }

  file { '/var/log/reprepro':
    ensure => directory,
  }

  file { '/var/run/reprepro':
    ensure => directory,
  }

  file { '/etc/reprepro':
    ensure => directory,
  }

  file { '/etc/reprepro.keytab':
    owner   => 'root',
    group   => 'root',
    mode    => '0400',
    content => $reprepro_keytab,
  }

  file { '/usr/local/bin/reprepro-mirror-update':
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0755',
    source  => 'puppet:///modules/openstack_project/reprepro/reprepro-mirror-update.sh',
  }

  cron { 'reprepro':
    ensure => absent,
  }

  ::openstack_project::reprepro { 'ubuntu-reprepro-mirror':
    confdir       => '/etc/reprepro/ubuntu',
    basedir       => '/afs/.openstack.org/mirror/ubuntu',
    distributions => 'openstack_project/reprepro/distributions.ubuntu.erb',
    updates_file  => 'puppet:///modules/openstack_project/reprepro/debuntu-updates',
    releases      => ['trusty'],
  }

  cron { 'reprepro ubuntu':
    user        => $user,
    hour        => '*/2',
    command     => 'flock -n /var/run/reprepro/ubuntu.lock reprepro-mirror-update /etc/reprepro/ubuntu mirror.ubuntu >>/var/log/reprepro/ubuntu-mirror.log 2>&1',
    environment => 'PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
    require     => [
       File['/usr/local/bin/reprepro-mirror-update'],
       File['/etc/afsadmin.keytab'],
       File['/etc/reprepro.keytab'],
       ::openstack_project::reprepro['ubuntu-reprepro-mirror'],
    ]
  }

  include ::gnupg

  gnupg_key { 'Ubuntu Archive':
    ensure     => present,
    key_id     => '40976EAF437D05B5',
    user       => 'root',
    key_server => 'hkp://keyserver.ubuntu.com',
    key_type   => 'public',
  }
}
