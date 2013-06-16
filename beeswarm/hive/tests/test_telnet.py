# Copyright (C) 2012 Johnny Vestergaard <jkv@unixcluster.dk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gevent
import gevent.monkey
from beeswarm.hive.helpers.common import create_socket
from beeswarm.hive.models.user import HiveUser
from beeswarm.hive.capabilities import telnet

gevent.monkey.patch_all()
from gevent.server import StreamServer

import unittest
import telnetlib
import tempfile
import sys
import os
import shutil

from beeswarm.hive.hive import Hive
from beeswarm.hive.models.session import Session
from beeswarm.hive.models.authenticator import Authenticator


class Telnet_Tests(unittest.TestCase):
    def setUp(self):
        self.work_dir = tempfile.mkdtemp()
        Hive.prepare_environment(self.work_dir)

    def tearDown(self):
        if os.path.isdir(self.work_dir):
            shutil.rmtree(self.work_dir)

    def test_invalid_login(self):
        """Tests if telnet server responds correctly to a invalid login attempt."""

        #curses dependency in the telnetserver need a STDOUT with file descriptor.
        sys.stdout = tempfile.TemporaryFile()

        #initialize capability and start tcp server
        sessions = {}
        users = {'test': HiveUser('test', 'test')}

        #provide valid login/pass to authenticator
        authenticator = Authenticator(users)
        Session.authenticator = authenticator

        options = {'enabled': 'True', 'port': 2503, 'max_attempts': 3}
        cap = telnet.telnet(sessions, options, users, self.work_dir)
        socket = create_socket(('0.0.0.0', 2503))
        server = StreamServer(socket, cap.handle_session)
        server.start()

        client = telnetlib.Telnet('localhost', 2503)
        #set this to 1 if having problems with this test
        client.set_debuglevel(0)

        #this disables all command negotiation.
        client.set_option_negotiation_callback(self.cb)

        #Expect username as first output
        reply = client.read_until('Username: ', 1)
        self.assertEquals('Username: ', reply)

        client.write('someuser' + '\r\n')
        reply = client.read_until('Password: ', 5)
        self.assertTrue(reply.endswith('Password: '))

        client.write('somepass' + '\r\n')
        reply = client.read_until('Invalid username/password\r\nUsername: ')
        self.assertTrue(reply.endswith('Invalid username/password\r\nUsername: '))

        server.stop()

    def test_valid_login(self):
        """Tests if telnet server responds correctly to a VALID login attempt."""

        #curses dependency in the telnetserver need a STDOUT with file descriptor.
        sys.stdout = tempfile.TemporaryFile()

        #initialize capability and start tcp server
        sessions = {}
        users = {'test': HiveUser('test', 'test')}

        #provide valid login/pass to authenticator
        authenticator = Authenticator(users)
        Session.authenticator = authenticator

        options = {'enabled': 'True', 'port': 2503, 'max_attempts': 3}
        cap = telnet.telnet(sessions, options, users, self.work_dir)
        socket = create_socket(('0.0.0.0', 2503))
        server = StreamServer(socket, cap.handle_session)
        server.start()

        client = telnetlib.Telnet('localhost', 2503)
        #set this to 1 if having problems with this test
        client.set_debuglevel(0)

        #this disables all command negotiation.
        client.set_option_negotiation_callback(self.cb)

        #Expect username as first output
        reply = client.read_until('Username: ', 1)
        self.assertEquals('Username: ', reply)

        client.write('test' + '\r\n')
        reply = client.read_until('Password: ', 5)
        self.assertTrue(reply.endswith('Password: '))

        client.write('test' + '\r\n')
        reply = client.read_until('$ ')
        self.assertTrue(reply.endswith('$ '))

        server.stop()

    def test_commands(self):
        """Tests the telnet commands"""

        #curses dependency in the telnetserver need a STDOUT with file descriptor.
        sys.stdout = tempfile.TemporaryFile()

        #initialize capability and start tcp server
        sessions = {}
        users = {'test': HiveUser('test', 'test')}

        #provide valid login/pass to authenticator
        authenticator = Authenticator(users)
        Session.authenticator = authenticator

        options = {'enabled': 'True', 'port': 2506, 'max_attempts': 3}
        cap = telnet.telnet(sessions, options, users, self.work_dir)
        socket = create_socket(('0.0.0.0', 2506))
        server = StreamServer(socket, cap.handle_session)
        server.start()

        client = telnetlib.Telnet('localhost', 2506)
        #set this to 1 if having problems with this test
        client.set_debuglevel(0)

        #this disables all command negotiation.
        client.set_option_negotiation_callback(self.cb)

        #Expect username as first output
        reply = client.read_until('Username: ', 1)
        self.assertEquals('Username: ', reply)

        client.write('test' + '\r\n')
        reply = client.read_until('Password: ', 5)
        self.assertTrue(reply.endswith('Password: '))

        client.write('test' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.endswith('$ '))

        # Command: ls
        client.write('ls -l' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.startswith('ls -l\r\n'))  # The server must echo the command.
        self.assertTrue(reply.endswith('$ '))

        # Command: echo
        client.write('echo this test is so cool' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.startswith('echo '))
        self.assertTrue('this test is so cool' in reply)
        self.assertTrue(reply.endswith('$ '))

        # Command: cd
        client.write('cd var' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.startswith('cd '))
        self.assertTrue(reply.endswith('$ '))

        # Command: pwd
        client.write('pwd' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.startswith('pwd'))
        self.assertTrue('/var' in reply)  # Since we have done 'cd var' before
        self.assertTrue(reply.endswith('$ '))

        # Command: uname
        client.write('uname -a' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.startswith('uname '))
        self.assertTrue(reply.endswith('$ '))

        # Command: cat
        client.write('cat /var/www/index.html' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.startswith('cat '))
        self.assertTrue('</html>' in reply)  # Make sure we have received the complete file
        self.assertTrue(reply.endswith('$ '))

        # Command: uptime
        client.write('uptime' + '\r\n')
        reply = client.read_until('$ ', 5)
        self.assertTrue(reply.startswith('uptime'))
        self.assertTrue(reply.endswith('$ '))

        server.stop()

    def cb(self, socket, command, option):
        return

if __name__ == '__main__':
    unittest.main()