# Universal Laboratory Automation Framework Guide

## I. Framework Design Overview

This automation framework's core concept is to define experimental workflows through JSON configuration files, which are then parsed and executed by a locally built dispatcher and execution agent. Each unit operation is encapsulated in an independent backend.py file.

## II. System Architecture Preparation

### 1. Core Components

```
1. JSON Configuration Parser (Dispatcher)
   - Responsible for parsing experiment configuration files
   - Converts configurations into executable operation sequences

2. Execution Engine (Execution Agent)
   - Executes operation sequences in order
   - Manages data flow between operations
   - Handles errors and exceptions

3. Unit Operation Modules (Backend Modules)
   - Each module corresponds to a specific experimental operation
   - Encapsulates interaction logic with specific instruments
   - Provides standardized interfaces
```

### 2. File Structure

Recommended file structure:

```
lab-automation/
├── src/
│   ├── dispatcher/
│   │   ├── __init__.py
│   │   ├── json_parser.py      # JSON parser
│   │   └── operation_mapper.py # Operation mapper
│   ├── executor/
│   │   ├── __init__.py
│   │   ├── agent.py            # Execution agent
│   │   └── error_handler.py    # Error handler
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── operation1.py       # Unit operation 1
│   │   ├── operation2.py       # Unit operation 2
│   │   └── ...
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_utils.py    # Logging utilities
│   │   └── data_utils.py       # Data processing utilities
│   └── main.py                 # Main program entry
├── templates/
│   └── experiment_template.json # Experiment template
├── data/                        # Data storage directory
├── logs/                        # Log directory
├── requirements.txt             # Dependency list
└── README.md                    # System documentation
```

## III. Building Steps

### 1. Define Standard Interface

First, define a standard interface for all unit operations to ensure they can be called uniformly:

```python
# src/backends/base_operation.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseOperation(ABC):
    """Base class for all unit operations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize operation

        Parameters:
        config: Operation configuration parameters
        """
        self.config = config
        self.validate_config()

    @abstractmethod
    def validate_config(self) -> None:
        """Validate configuration parameters"""
        pass

    @abstractmethod
    async def execute(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute operation

        Parameters:
        input_data: Input data, possibly from previous operation

        Returns:
        Operation result data
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources"""
        pass
```

### 2. Implement Unit Operation Modules

For each experimental operation, create a class that inherits from BaseOperation:

```python
# src/backends/operation1.py
import asyncio
from typing import Dict, Any, Optional
from src.backends.base_operation import BaseOperation

class Operation1(BaseOperation):
    """Example operation 1 - e.g., temperature control"""

    def validate_config(self) -> None:
        """Validate configuration parameters"""
        required_params = ['target_temperature', 'duration']
        for param in required_params:
            if param not in self.config:
                raise ValueError(f"Missing required parameter: {param}")

        # Validate parameter ranges
        if not (20 <= self.config['target_temperature'] <= 100):
            raise ValueError("Target temperature must be in range 20-100°C")

    async def execute(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute temperature control operation"""
        print(f"Setting temperature to {self.config['target_temperature']}°C")

        # Code to communicate with actual device
        # For example, via serial port or network connection

        # Simulate operation execution
        await asyncio.sleep(2)

        # Monitor temperature until target is reached
        current_temp = 25  # Initial temperature, should be read from device
        while abs(current_temp - self.config['target_temperature']) > 0.5:
            # Simulate temperature change
            current_temp += 0.5 * (self.config['target_temperature'] - current_temp)
            print(f"Current temperature: {current_temp:.1f}°C")
            await asyncio.sleep(1)

        # Maintain for specified duration
        print(f"Target temperature reached, maintaining for {self.config['duration']} seconds")
        await asyncio.sleep(self.config['duration'])

        return {
            'operation': 'temperature_control',
            'target_temperature': self.config['target_temperature'],
            'final_temperature': current_temp,
            'duration': self.config['duration']
        }

    def cleanup(self) -> None:
        """Clean up resources"""
        print("Shutting down temperature controller")
        # Actual cleanup code
```

### 3. Implement JSON Parser

Create a parser to convert JSON configuration into operation sequences:

```python
# src/dispatcher/json_parser.py
import json
from typing import Dict, Any, List

class JsonParser:
    """JSON configuration parser"""

    def __init__(self, config_path: str):
        """
        Initialize parser

        Parameters:
        config_path: JSON configuration file path
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load JSON configuration"""
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def get_metadata(self) -> Dict[str, Any]:
        """Get experiment metadata"""
        return self.config.get('metadata', {})

    def get_operations(self) -> List[Dict[str, Any]]:
        """Get operation sequence"""
        return self.config.get('operations', [])

    def validate(self) -> bool:
        """Validate configuration format"""
        # Check required top-level fields
        required_fields = ['metadata', 'operations']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Configuration missing required field: {field}")

        # Check operation sequence
        operations = self.get_operations()
        if not operations:
            raise ValueError("Operation sequence is empty")

        # Check each operation
        for i, op in enumerate(operations):
            if 'type' not in op:
                raise ValueError(f"Operation #{i+1} missing 'type' field")
            if 'params' not in op:
                raise ValueError(f"Operation #{i+1} missing 'params' field")

        return True
```

### 4. Implement Operation Mapper

Create a mapper to map operation types to corresponding backend modules:

```python
# src/dispatcher/operation_mapper.py
from typing import Dict, Type, Any
from src.backends.base_operation import BaseOperation
# Import all operation modules
from src.backends.operation1 import Operation1
from src.backends.operation2 import Operation2
# Import more operations...

class OperationMapper:
    """Operation type mapper"""

    # Mapping from operation type to class
    _operation_map: Dict[str, Type[BaseOperation]] = {
        'temperature_control': Operation1,
        'mixing': Operation2,
        # Add more operation mappings...
    }

    @classmethod
    def get_operation_class(cls, operation_type: str) -> Type[BaseOperation]:
        """
        Get the class corresponding to an operation type

        Parameters:
        operation_type: Operation type name

        Returns:
        Corresponding operation class

        Exceptions:
        ValueError: If operation type doesn't exist
        """
        if operation_type not in cls._operation_map:
            raise ValueError(f"Unknown operation type: {operation_type}")

        return cls._operation_map[operation_type]

    @classmethod
    def create_operation(cls, operation_type: str, config: Dict[str, Any]) -> BaseOperation:
        """
        Create operation instance

        Parameters:
        operation_type: Operation type
        config: Operation configuration

        Returns:
        Operation instance
        """
        operation_class = cls.get_operation_class(operation_type)
        return operation_class(config)
```

### 5. Implement Execution Agent

Create an execution agent responsible for executing operations in sequence:

```python
# src/executor/agent.py
import asyncio
import logging
from typing import Dict, Any, List, Optional

from src.dispatcher.json_parser import JsonParser
from src.dispatcher.operation_mapper import OperationMapper

class ExecutionAgent:
    """Experiment execution agent"""

    def __init__(self, config_path: str):
        """
        Initialize execution agent

        Parameters:
        config_path: Configuration file path
        """
        self.logger = logging.getLogger(__name__)
        self.parser = JsonParser(config_path)
        self.operations = []
        self.results = {}

    async def prepare(self) -> None:
        """Prepare execution environment"""
        self.logger.info("Validating configuration file...")
        self.parser.validate()

        self.logger.info("Loading operation sequence...")
        operation_configs = self.parser.get_operations()

        for op_config in operation_configs:
            op_type = op_config['type']
            op_params = op_config['params']

            self.logger.info(f"Creating operation: {op_type}")
            operation = OperationMapper.create_operation(op_type, op_params)
            self.operations.append(operation)

    async def execute(self) -> Dict[str, Any]:
        """Execute all operations"""
        self.logger.info("Starting experiment execution...")

        previous_result = None
        all_results = []

        for i, operation in enumerate(self.operations):
            op_name = operation.__class__.__name__
            self.logger.info(f"Executing operation {i+1}/{len(self.operations)}: {op_name}")

            try:
                result = await operation.execute(previous_result)
                previous_result = result
                all_results.append(result)
                self.logger.info(f"Operation {op_name} executed successfully")
            except Exception as e:
                self.logger.error(f"Operation {op_name} execution failed: {str(e)}")
                # Add error handling logic here
                raise

        self.logger.info("Experiment execution completed")
        return {
            "metadata": self.parser.get_metadata(),
            "results": all_results
        }

    async def cleanup(self) -> None:
        """Clean up resources"""
        self.logger.info("Cleaning up resources...")
        for operation in self.operations:
            try:
                operation.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up operation {operation.__class__.__name__}: {str(e)}")
```

### 6. Create Main Program Entry

```python
# src/main.py
import asyncio
import argparse
import logging
import json
import os
from datetime import datetime

from src.executor.agent import ExecutionAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main program entry"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Universal Experiment Automation Framework")
    parser.add_argument("--config", required=True, help="Experiment configuration file path")
    parser.add_argument("--output", help="Results output file path")
    args = parser.parse_args()

    # Create execution agent
    agent = ExecutionAgent(args.config)

    try:
        # Prepare execution environment
        await agent.prepare()

        # Execute experiment
        results = await agent.execute()

        # Save results
        if args.output:
            output_path = args.output
        else:
            # Create default output path with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "data"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"results_{timestamp}.json")

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Experiment results saved to: {output_path}")

    except Exception as e:
        logging.error(f"Experiment execution failed: {str(e)}")
        raise
    finally:
        # Clean up resources
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## IV. JSON Configuration File Format

Define a standard JSON configuration file format:

```json
{
  "metadata": {
    "experiment_id": "EXP-001",
    "description": "Example experiment",
    "created_by": "Researcher name",
    "created_at": "2024-07-01T10:00:00Z"
  },
  "operations": [
    {
      "type": "temperature_control",
      "params": {
        "target_temperature": 50,
        "duration": 300
      }
    },
    {
      "type": "mixing",
      "params": {
        "speed": 500,
        "duration": 120
      }
    },
    {
      "type": "sampling",
      "params": {
        "volume": 5,
        "container": "vial_1"
      }
    }
  ]
}
```

## V. Teaching Other Laboratories

### 1. Framework Structure Explanation

Explain the core components and working principles of the framework to other laboratories:

```
1. Configuration File (JSON) → Defines experiment workflow and parameters
2. Parser (Dispatcher) → Parses configuration and maps to operations
3. Execution Agent → Executes operations in sequence
4. Backend Modules → Encapsulate device interactions
```

### 2. How to Add New Unit Operations

Guide them on how to create backend modules for their own devices and operations:

```
1. Create a new operation class, inheriting from BaseOperation
2. Implement three core methods:
   - validate_config(): Validate parameters
   - execute(): Execute operation
   - cleanup(): Clean up resources
3. Register the new operation in OperationMapper
```

### 3. Configuration File Writing Guide

Provide guidelines for writing configuration files:

```
1. metadata section: Contains basic experiment information
2. operations section: Defines operation sequence
   - Each operation must specify type and params
   - Parameters in params depend on specific operation requirements
3. Operation order: Operations will be executed in the order they appear in the configuration file
4. Data flow: Results from previous operations can be passed to subsequent operations
```

### 4. Practical Case Demonstration

Provide a complete example, including:

```
1. Sample configuration file
2. Backend implementations for several common operations
3. Run the example and show results
```

## VI. Materials to Prepare

To help other laboratories replicate this framework, you need to prepare the following materials:

### 1. Code Templates

```
- Basic framework code (as described above)
- Sample backend modules
- Configuration file templates
```

### 2. Documentation

```
- Architecture design document
- API reference manual
- Configuration file format specification
- Unit operation development guide
```

### 3. Teaching Materials

```
- Framework overview presentation
- Code walkthrough tutorial
- Frequently asked questions
- Troubleshooting guide
```

### 4. Sample Projects

```
- Simple complete example project
- Complex example with multiple operation types
- Error handling examples
```

## VII. Implementation Recommendations

### 1. Phased Implementation

Recommend other laboratories implement in phases:

```
1. Phase 1: Build basic framework, implement 1-2 simple operations
2. Phase 2: Add more operations, improve error handling
3. Phase 3: Optimize performance, enhance reliability
```

### 2. Testing Strategy

```
1. Unit testing: Test individual operation modules
2. Integration testing: Test operation sequence execution
3. Mock testing: Test with simulated devices
4. Real device testing: Test with actual devices
```

### 3. Version Control

```
1. Use Git for code management
2. Define version numbers for configuration file format
3. Document API changes
```

## VIII. Summary

Through these steps, other laboratories can build a similar automation framework tailored to their own workflows and devices. Key points are:

1. **Modular Design**: Each unit operation is an independent module
2. **Standardized Interface**: All operations follow the same interface
3. **Declarative Configuration**: Experiment workflows declared via JSON files
4. **Extensibility**: Easy to add new operation types

This design allows the framework to adapt to various experimental scenarios, not limited to specific workflows or devices.