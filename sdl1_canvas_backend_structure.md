# SDL1 Canvas Backend: Codebase Structure and Documentation

This document provides a comprehensive overview of the SDL1 Canvas Backend codebase structure, detailing the purpose and functionality of each key component. This can serve as a reference for other laboratories looking to implement similar automated electrochemical experiment systems.

## Repository Overview

The SDL1 Canvas Backend is a modular system for automating electrochemical experiments, integrating:
- BioLogic potentiostat control
- Opentrons liquid handling
- Arduino-controlled pumps
- Real-time data visualization
- Experiment workflow management

## Top-Level Directory

- **README.md**: Project overview, installation guide, and usage instructions
- **requirements.txt**: Python dependency list
- **lab_automation_framework_guide.md**: Universal laboratory automation framework design guide
- **package.json**: Node.js package configuration for web components

## Main Directory Structure

### 1. biologic/ - BioLogic Device Interface

This directory contains code for interacting with BioLogic electrochemical workstations:

#### Core Files

- **__init__.py**:
  - Initializes the module and provides the main connection functionality
  - Defines the `connect()` function to establish connection with BioLogic devices
  - Exports key classes and constants

- **channel.py**:
  - Implements the `Channel` class for controlling individual channels on BioLogic devices
  - Handles channel configuration, technique execution, and data acquisition
  - Provides methods for running techniques and monitoring channel status

- **data.py**:
  - Defines data structures for electrochemical measurements
  - Implements the `TechniqueData` base class for all technique data containers
  - Provides serialization/deserialization methods for data exchange

- **deviceinfo.py**:
  - Contains device information and configuration classes
  - Defines `DeviceInfo` and `ChannelInfo` classes
  - Handles device capabilities and limitations

- **json.py**:
  - Provides JSON serialization and deserialization utilities
  - Implements decorators for converting between Python objects and JSON
  - Supports custom type conversions

- **metadata.py**:
  - Handles experiment metadata processing
  - Stores information about experiment conditions, device settings, and timestamps
  - Provides structured access to experiment context

- **params.py**:
  - Defines technique parameters and validation logic
  - Implements the `TechniqueParams` base class for all technique parameter containers
  - Provides parameter validation and conversion utilities

- **runner.py**:
  - Implements the `TechniqueRunner` class for managing technique execution
  - Handles data collection, experiment flow control, and error management
  - Provides asynchronous iteration over experiment data

- **technique.py**:
  - Defines the base `Technique` class that all electrochemical techniques inherit from
  - Implements common functionality for parameter validation, data unpacking, and device communication
  - Provides the framework for technique implementation

#### biologic/techniques/ - Electrochemical Technique Implementations

- **ca.py**:
  - Implements Chronoamperometry (CA) technique
  - Measures current response to applied potential steps
  - Defines `CAParams`, `CAData`, and `CATechnique` classes

- **cp.py**:
  - Implements Chronopotentiometry (CP) technique
  - Controls current and measures potential over time
  - Defines `CPParams`, `CPData`, and `CPTechnique` classes

- **cv.py**:
  - Implements Cyclic Voltammetry (CV) technique
  - Performs potential sweeps and measures current response
  - Defines `CVParams`, `CVData`, and `CVTechnique` classes

- **ocv.py**:
  - Implements Open Circuit Voltage (OCV) technique
  - Measures potential without current flow
  - Defines `OCVParams`, `OCVData`, and `OCVTechnique` classes

- **peis.py**:
  - Implements Potentiostatic Electrochemical Impedance Spectroscopy (PEIS)
  - Measures impedance across frequency range
  - Defines `PEISParams`, `PEISData`, and `PEISTechnique` classes

- **lp.py**:
  - Implements Linear Polarization (LP) technique
  - Performs linear potential sweeps
  - Defines `LPParams`, `LPData`, and `LPTechnique` classes

- **cpp.py**:
  - Implements Chronopotentiometry with Potential (CPP) technique
  - Combines features of CP and CA techniques
  - Defines `CPPParams`, `CPPData`, and `CPPTechnique` classes

- **pzir.py**:
  - Implements specialized impedance-related techniques
  - Provides additional impedance analysis capabilities
  - Defines corresponding parameter and data classes

#### biologic/extras/ - Auxiliary Tools

- **blfind.py**:
  - BioLogic device discovery tool
  - Scans for connected devices via USB and Ethernet
  - Provides detailed device information

- **run_tech.py**:
  - Standalone tool for running individual electrochemical techniques
  - Allows direct execution of techniques without the full framework
  - Supports JSON input/output for technique parameters and results

### 2. src/ - Main Source Code

This directory contains the core application code:

#### Main Entry Points

- **main.py**:
  - Primary program entry point
  - Processes command-line arguments and manages experiment flow
  - Supports three operation modes: single experiment, batch processing, and template generation
  - Handles device initialization, experiment execution, and resource cleanup
  - Implements error handling and logging

- **run_multi_technique.py**:
  - Multi-technique experiment execution script
  - Reads experiment sequences and parameters from YAML configuration files
  - Supports continuous execution of multiple electrochemical techniques
  - Provides real-time web visualization
  - Supports both mock mode and real device mode

- **react_proxy_server.py**:
  - React frontend proxy server
  - Bridges WebSocket backend and React frontend
  - Handles HTTP request proxying and WebSocket communication
  - Enables unified access to both data and visualization interfaces

- **web_visualization.py**:
  - Web visualization service
  - Provides real-time data visualization through web interface
  - Configures visualization parameters based on technique type
  - Manages data streaming to web clients

#### src/config/ - Configuration Module

- **device_config.py**:
  - Device configuration classes and utilities
  - Defines configuration parameters for Opentrons, Arduino, and BioLogic devices
  - Provides validation and default values for device settings

- **experiment_config.py**:
  - Experiment configuration classes and utilities
  - Defines parameters for deposition and characterization experiments
  - Handles experiment sequence configuration and validation

#### src/core/ - Core Functionality

##### src/core/devices/ - Device Control

- **base_device.py**:
  - Abstract base class for all device controllers
  - Defines common interface for device connection, operation, and disconnection
  - Implements shared functionality for error handling and status reporting

- **opentrons_device.py**:
  - Opentrons liquid handling robot controller
  - Manages connection to OT-2 robot via API
  - Implements methods for well selection, liquid transfer, and tip management
  - Handles protocol execution and error recovery

- **arduino_device.py**:
  - Arduino controller interface
  - Manages serial communication with Arduino-based pump controllers
  - Implements commands for fluid control, valve operation, and system monitoring
  - Provides error detection and recovery mechanisms

- **biologic_device.py**:
  - BioLogic device interface
  - Wraps the lower-level biologic module with experiment-specific functionality
  - Provides simplified methods for running common electrochemical techniques
  - Handles data conversion between BioLogic format and experiment framework

- **mock_biologic_device.py**:
  - Mock implementation of BioLogic device for testing
  - Simulates device behavior without requiring actual hardware
  - Generates realistic test data for all supported techniques
  - Useful for development, testing, and demonstration

##### src/core/experiment/ - Experiment Management

- **experiment_manager.py**:
  - Experiment manager that coordinates devices and workflow
  - Orchestrates the complete experimental process
  - Manages transitions between deposition and characterization phases
  - Implements error handling and recovery strategies
  - Coordinates data collection and storage across multiple devices

#### src/utils/ - Utility Functions

- **config_loader.py**:
  - Configuration loader for experiment parameters
  - Loads experiment parameters from CSV or Excel files
  - Supports parameter validation and default values
  - Provides template generation for new experiment configurations

- **data_processing.py**:
  - Data processing module for electrochemical data
  - Implements the core data processing pipeline
  - Contains classes for data acquisition, processing, storage, and visualization
  - Defines the `ExperimentController` class that coordinates the entire experiment
  - Handles real-time data processing and visualization

- **data_utils.py**:
  - Data utility functions
  - Provides helper methods for data conversion, filtering, and analysis
  - Implements common electrochemical data processing algorithms
  - Supports data export in various formats

- **logging_utils.py**:
  - Logging utilities
  - Configures logging for different components
  - Implements structured logging with context information
  - Provides methods for log file management

- **websocket_server.py**:
  - WebSocket server for real-time data transmission
  - Handles client connections and message routing
  - Broadcasts data updates to connected clients
  - Manages connection lifecycle and error handling

- **websocket_handler.py**:
  - WebSocket data handler
  - Processes data for transmission over WebSocket
  - Formats data according to client requirements
  - Implements data filtering and compression

- **enhanced_websocket_server.py**:
  - Enhanced WebSocket server with additional features
  - Supports multiple data channels and client types
  - Provides authentication and session management
  - Implements more sophisticated message routing and filtering

#### src/examples/ - Example Code

- **data_processing_example.py**:
  - Data processing example demonstrating the framework
  - Shows how to set up and run a complete experiment
  - Illustrates data processing pipeline configuration
  - Provides a reference implementation for custom experiments

#### src/web-react/ and src/biologic-react-app/ - Frontend Interfaces

These directories contain React frontend applications for real-time monitoring and control:

- **src/web-react/**:
  - Main React frontend application
  - Implements real-time data visualization dashboard
  - Provides experiment control interface
  - Connects to backend via WebSocket

- **src/biologic-react-app/**:
  - Specialized React application for BioLogic device control
  - Offers detailed device configuration interface
  - Provides technique-specific parameter settings
  - Visualizes technique-specific data formats

### 3. templates/ - Experiment Templates

- **experiment_template.yaml**:
  - Complete experiment configuration template
  - Includes all available parameters and options
  - Contains detailed comments explaining each parameter
  - Serves as reference for creating custom configurations

- **simple_experiment.yaml**:
  - Simplified experiment configuration template
  - Includes only essential parameters
  - Provides a starting point for basic experiments
  - Easier to understand for new users

### 4. test_data/ - Test Data

Contains test experiment data files:

- **characterization/**: Sample characterization data files
- **deposition/**: Sample deposition data files
- **metadata.json**: Example experiment metadata

## System Workflow

1. **Configuration Phase**:
   - User defines experiment parameters via command line or configuration files
   - System loads and validates configuration
   - Experiment directories are created

2. **Initialization Phase**:
   - Connections established to required devices (BioLogic, Opentrons, Arduino)
   - Data processing components initialized
   - WebSocket server started for real-time monitoring

3. **Execution Phase**:
   - Electrochemical technique sequences created
   - Techniques executed in sequence
   - Data collected, processed, and visualized in real-time
   - Results saved to file system

4. **Cleanup Phase**:
   - Device connections closed
   - Resources properly released
   - Final experiment summary generated

## Key Design Features

1. **Modular Architecture**: Each component (device control, data processing, visualization) is an independent module
2. **Extensibility**: Easy to add new electrochemical techniques or device support
3. **Flexible Configuration**: Configure experiments via JSON/YAML files or command line parameters
4. **Real-time Monitoring**: WebSocket and graphical interface for real-time experiment monitoring
5. **Error Handling**: Comprehensive error detection and recovery mechanisms
6. **Data Management**: Structured data storage and processing pipeline

This system's core value lies in automating complex electrochemical experiments through simple configuration, while providing real-time data monitoring and analysis capabilities.
