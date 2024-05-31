import json
import argparse
from urllib.parse import urlparse
from base64 import b64encode, b64decode


def parse_har_file(input_file, output_file):
    wstalker_out = ''

    with open(input_file, 'r', encoding='UTF-8') as f:
        har_data = json.loads(f.read())

    entries = har_data['log']['entries']

    for entry in entries:
        if not entry['request']['url'].startswith(('http://', 'https://')):  # skip ws://
            continue

        # ------------------------------ Request ------------------------------
        request = entry['request']

        method = request['method'].upper()
        parsed_url = urlparse(request['url'])
        path_query = parsed_url.path \
                     + ('?' + parsed_url.query if parsed_url.query else '') \
                     + ('#' + parsed_url.fragment if parsed_url.fragment else '')
        http_version = request['httpVersion'].upper()

        headers = request['headers']
        header_dict = {header['name']: header['value'] for header in headers if not header['name'].startswith(':')}
        if 'Host' not in header_dict:  # HTTP/2 requests lack a Host header, so we construct it ourselves.
            header_dict['Host'] = parsed_url.netloc

        request_body = request.get('postData', {}).get('text', '').encode()

        request_data = f'{method} {path_query} {http_version}\r\n'.encode()
        for name, value in header_dict.items():
            request_data += f'{name}: {value}\r\n'.encode()
        request_data += b'\r\n'
        request_data += request_body

        # ------------------------------ Response ------------------------------
        response = entry['response']

        status_code = response['status']
        status_text = response['statusText']
        http_version = response['httpVersion'].upper()

        header_dict = {header['name']: header['value'] for header in response['headers']}

        response_body = response.get('content', {}).get('text', '').encode()
        if response.get('content', {}).get('encoding', '') == 'base64':
            response_body = b64decode(response_body)

        response_data = f'{http_version} {status_code} {status_text}\r\n'.encode()
        for name, value in header_dict.items():
            response_data += f'{name}: {value}\r\n'.encode()
        response_data += b'\r\n'
        response_data += response_body

        # Write data
        wstalker_out += b64encode(request_data).decode() + ','
        wstalker_out += b64encode(response_data).decode() + ','
        wstalker_out += f'{method},{parsed_url.scheme}://{parsed_url.netloc}\n'

    # Write extracted data to CSV
    with open(output_file, 'w') as csvfile:
        csvfile.write(wstalker_out)


def main():
    parser = argparse.ArgumentParser(description="Convert HAR file to WStalker CSV.")
    parser.add_argument('-i', '--input', type=str, required=True, help='Input HAR file')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output CSV file')
    args = parser.parse_args()

    parse_har_file(args.input, args.output)


if __name__ == '__main__':
    main()
