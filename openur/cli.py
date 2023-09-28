import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='OpenUR command line interface')
    parser.add_argument('command', choices=['make'], help='the command to create the rtde configuration file')
    parser.add_argument('directory', help='the directory to create the rtde_configuration.xml file in')
    args = parser.parse_args()

    if args.command == 'make':
        make(args.directory)

def make(directory):
    content = '''<?xml version="1.0"?>
<rtde_config>
	<recipe key="rco">
		<field name="actual_q" type="VECTOR6D"/>
	</recipe>
	<recipe key="rci">
		<field name = "speed_slider_mask" type = "UINT32"/>
		<field name = "speed_slider_fraction" type = "DOUBLE"/>
	</recipe>
</rtde_config>
'''

    path = os.path.join(directory, 'rtde_configuration.xml')
    with open(path, 'w') as f:
        f.write(content)
    absolute_path = os.path.abspath(path)
    print(f'File created at: {absolute_path}')
