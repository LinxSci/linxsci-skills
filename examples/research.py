"""Run from the repository root after installing the package and configuring setup."""
import json
import sys
from linxsci import LinxSciClient, LinxSciError


def main():
    try:
        client = LinxSciClient(timeout=60)
        response = client.search("graph neural networks")
        print("HTTP 状态：", response.status)
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        return 0
    except LinxSciError as error:
        print("HTTP 状态：", error.status, file=sys.stderr)
        print("错误码：", error.error_code, file=sys.stderr)
        print("上游/代理请求 ID：", error.request_id, file=sys.stderr)
        print("LinxSci 框架请求 ID：", error.framework_request_id, file=sys.stderr)
        if error.execution_uncertain:
            print("请先核查执行与计费结果，不要直接重复请求。", file=sys.stderr)
        return 1
    except (ValueError, OSError):
        print("请检查服务配置、输入参数及响应是否为 JSON。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
