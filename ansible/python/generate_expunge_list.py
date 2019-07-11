#!/usr/bin/python

# Generate expunge list based on results directory
#
# Given a directory path it finds all test failures and produces an
# expunge list you can use with fstests's check.sh -E option to let you
# then skip those tests.

import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description='generate_expunge_list')
    parser.add_argument('filesystem', metavar='<filesystem name>', type=str,
                        help='filesystem which was tested')
    parser.add_argument('results', metavar='<directory with results>', type=str,
                        help='directory with results file')
    parser.add_argument('outputdir', metavar='<output directory>', type=str,
                        help='The directory where to generate the expunge lists to')
    args = parser.parse_args()

    all_files = os.listdir(args.results)

    for root, dirs, all_files in os.walk(args.results):
        for fname in all_files:
            f = os.path.join(root, fname)
            #sys.stdout.write("%s\n" % f)
            if os.path.isdir(f):
                continue
            if not os.path.isfile(f):
                continue
            if not f.endswith('.bad'):
                continue

            # f may be results/oscheck-xfs/4.19.0-4-amd64/xfs/generic/091.out.bad
            bad_file_list = f.split("/")
            bad_file_list_len = len(bad_file_list) - 1
            bad_file = bad_file_list[bad_file_list_len]
            test_type = bad_file_list[bad_file_list_len-1]
            section = bad_file_list[bad_file_list_len-2]
            kernel = bad_file_list[bad_file_list_len-3]

            bad_file_parts = bad_file.split(".")
            bad_file_part_len = len(bad_file_parts) - 1
            bad_file_test_number = bad_file_parts[bad_file_part_len - 2]
            # This is like for example generic/091
            test_failure_line = test_type + '/' + bad_file_test_number

            # now to stuff this into expunge files such as:
            # path/4.19.17/xfs/unassigned/xfs_nocrc.txt
            output_dir = args.outputdir + '/' + kernel + '/' + args.filesystem + '/'
            output_dir += 'unassigned/'
            output_file = output_dir + section + '.txt'

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            # We want to now add entries like generic/xxx where xxx is a digit
            output = open(output_file, "a+")
            output.write("%s\n" % test_failure_line)
            output.close()

if __name__ == '__main__':
    main()
