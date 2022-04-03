import dataclasses
import datetime
import json
import pathlib

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

BEARER_TOKEN = ""


@dataclasses.dataclass(frozen=True)
class Point:
    x: int
    y: int

@dataclasses.dataclass(frozen=True)
class PointHistory:
    point: Point
    username: str
    lastModifiedTimestamp: int

def generate_output_path(start: Point, end: Point) -> pathlib.Path:
    output_path = pathlib.Path(f"./start_{start.x}_{start.y}-end_{end.x}_{end.y}.json")
    return output_path

def generate_points_in_polygon(start: Point, end: Point) -> list[Point]:
    enclosed_points = set()

    for x in range(start.x, end.x + 1):
        for y in range(start.y, end.y + 1):
            enclosed_points.add(Point(x=x, y=y))

    return list(enclosed_points)

def generate_mutation_params(points: list[Point]) -> str:
    mutation_strings = [f"$input{n}: ActInput!" for n,i in enumerate(points)]
    return f"""mutation({", ".join(mutation_strings)})""" + " {"

def generate_acts(points: list[Point]) -> str:
    def generate_act_string(n: int) -> str:
        act_string = """
            inputAct""" + str(n) + """: act(input: $input""" + str(n) + """) {
                data {
                    ...on BasicMessage {
                        id
                        data {
                            ...on GetTileHistoryResponseMessageData {
                                lastModifiedTimestamp
                                userInfo {
                                    userID
                                    username
                                }
                            }
                        }
                    }
                }
            }
        """
        return act_string
    return "\n".join(generate_act_string(n) for n,i in enumerate(points))


def main() -> None:
    start = Point(x=334, y=78)
    end = Point(x=399, y=131)

    points = generate_points_in_polygon(start, end)

    mut_string = generate_mutation_params(points)
    act_strings = generate_acts(points)

    query = mut_string + act_strings + "\t\t\n}"

    variables = {
        f"input{n}": {
            "actionName": "r/replace:get_tile_history",
            "PixelMessageData": {
                "coordinate": {
                    "x": i.x,
                    "y": i.y
                },
                "colorIndex": 0,
                "canvasIndex": 0
            }
        }
        for n,i in enumerate(points)
    }

    transport = RequestsHTTPTransport(
        url="https://gql-realtime-2.reddit.com/query",
        headers={
            "Authorization": f"Bearer {BEARER_TOKEN}"
        }
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)

    result = client.execute(gql(query), variable_values=variables)

    output_path = generate_output_path(start, end)

    with output_path.open("w+") as fp:
        json.dump(result, fp, indent=4)

    

if __name__ == "__main__":
    main()
