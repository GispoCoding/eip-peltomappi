import logging

LOGGER = logging.getLogger("peltomappi")

# disable pyogrio logging, makes logs more confusing
logging.getLogger("pyogrio").setLevel(logging.CRITICAL)

logging.basicConfig(
    format="%(asctime)s %(levelname)-4s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.DEBUG,
)
