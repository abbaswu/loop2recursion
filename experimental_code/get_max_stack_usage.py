#!/usr/bin/env python3

import argparse
import json

from extract_updates_to_call_stacks import extract_updates_to_call_stacks
from get_function_to_shift_stack_frame import get_function_to_shift_stack_frame
from parse_memory_trace_file import parse_memory_trace_file
from reduce_coroutine import reduce_coroutine


def parse_command_line_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input', type=str, required=True, help='input memtrace file path')
    parser.add_argument('-o', '--output', type=str, required=True, help='output JSON file path')
    parser.add_argument('--stack-frame-shifts', type=str, required=False, default='', help='JSON file containing a list of how much to shift each stack frame by (such as [0, -1200], which means shift first stack frame by 0, and second stack frame by -1200). Used for UWLalloc.')
    
    args = parser.parse_args()

    input_memtrace_file_path = args.input
    output_json_file_path = args.output
    
    if args.stack_frame_shifts:
        with open(args.stack_frame_shifts, 'r') as fp:
            stack_frame_shifts = json.load(fp)
    else:
        stack_frame_shifts = None

    return input_memtrace_file_path, output_json_file_path, stack_frame_shifts


def main():
    input_memtrace_file_path, output_json_file_path, stack_frame_shifts = parse_command_line_arguments()
    
    memtrace_record_iterable = parse_memory_trace_file(input_memtrace_file_path)
    
    new_stack_frames = (new_stack_frame for update in extract_updates_to_call_stacks(memtrace_record_iterable) for new_stack_frame in update)
    
    if stack_frame_shifts:
        function_to_shift_stack_frame = get_function_to_shift_stack_frame(stack_frame_shifts)
        new_stack_frames = (function_to_shift_stack_frame(stack_frame) for stack_frame in new_stack_frames)
    
    min_address_coroutine = reduce_coroutine(min)
    next(min_address_coroutine)
    
    max_address_coroutine = reduce_coroutine(max)
    next(max_address_coroutine)
    
    for new_stack_frame in new_stack_frames:
        start_address = new_stack_frame['start_address']
        end_address = new_stack_frame['end_address']
        
        max_address = max_address_coroutine.send(start_address)
        min_address = min_address_coroutine.send(end_address)
    
    max_stack_usage_dict = {'stack_size': max_address - min_address}
    
    with open(output_json_file_path, 'w') as fp:
        json.dump(max_stack_usage_dict, fp)

if __name__ == '__main__':
    main()

