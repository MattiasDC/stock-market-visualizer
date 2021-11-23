# stock-market-visualizer

stock-market-visualizer is a [Dash](https://dash.plotly.com/) application that can be used to explore stocks and indicators over time. It's uses the [stock-market-engine](https://bitbucket.org/MattiasDC/stock-market-engine.git) microservice.

## Installation

Use [docker](https://www.docker.com/) to install docker and then build stock-market-engine.

```bash
git clone https://bitbucket.org/MattiasDC/stock-market-visualizer.git
cd stock-market-visualizer
# change docker-compose-dev.yml to point to your stock-market-engine image
docker-compose -f docker-compose-dev.yml build
docker-compose -f docker-compose-dev.yml up
```

Open a web browser at 0.0.0.0:/sme and have fun!

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)