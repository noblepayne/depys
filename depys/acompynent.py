import contextlib

import compynent


class System(compynent.System):
    @contextlib.asynccontextmanager
    async def start(self, keys: dict = None):
        """Modified from compynent upstream to support async"""
        system_map = {}
        async with contextlib.AsyncExitStack() as stack:
            for component_name in self.order:
                config = self.components[component_name]
                component_context = config["constructor"](
                    **{
                        dep_alias: system_map[dep_name]
                        for dep_name, dep_alias in config["aliases"].items()
                    }
                )
                if hasattr(component_context, "__aenter__"):
                    system_map[component_name] = await stack.enter_async_context(component_context)
                else:
                    system_map[component_name] = stack.enter_context(component_context)
            yield system_map
