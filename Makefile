OUTPUT_DIR=build
REPORT_DIR=reports

all: unittests specs features igloo-tests doc main

$(OUTPUT_DIR)/Makefile:
	@make prepare

ifeq ($(OS),Windows_NT)
  CONFIGURE=./configure.bat
  LAUNCH_PREFIX=start
  LAUNCH_SUFFIX=
  CONFIG=Debug
  BINARY_DIR=Debug/
  BINARY_SUFFIX=.exe
  MEMCHECK=drmemory.exe
else
  CONFIGURE=./configure.sh
  UNAME=$(shell uname -s)
  LAUNCH_PREFIX=
  LAUNCH_SUFFIX=&
  CONFIG=Debug
  BINARY_DIR=
  BINARY_SUFFIX=
  MEMCHECK=valgrind --leak-check=full --track-origins=yes --xml=yes --xml-file=$(REPORT_DIR)/memcheck.xml 
endif

CUCUMBER_FEATURES_PATH=tests/feature
CUCUMBER=cd $(CUCUMBER_FEATURES_PATH) && cucumber

$(OUTPUT_DIR)/CMakeFiles:
	$(CONFIGURE) -DCMAKE_BUILD_TYPE=$(CONFIG)

$(REPORT_DIR):
	$(CONFIGURE)

.PHONY: prepare
prepare: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target googlemock
	@cmake --build $(OUTPUT_DIR) --target boost
	@cmake --build $(OUTPUT_DIR) --target cppspec
	@cmake --build $(OUTPUT_DIR) --target igloo
	@cmake --build $(OUTPUT_DIR) --target cucumber-cpp
	@$(CONFIGURE)

.PHONY: main
main: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target CMake_Project_Template

.PHONY: test
test: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target dummy_test
	@cmake --build $(OUTPUT_DIR) --target test

.PHONY: unittests
unittests: $(OUTPUT_DIR)/CMakeFiles 
	@cmake --build $(OUTPUT_DIR) --target unittests
	$(OUTPUT_DIR)/tests/unit/$(BINARY_DIR)/unittests$(BINARY_SUFFIX) --gtest_shuffle

.PHONY: specs
specs: $(OUTPUT_DIR)/CMakeFiles 
	@cmake --build $(OUTPUT_DIR) --target specs
	$(OUTPUT_DIR)/tests/spec/$(BINARY_DIR)/specs$(BINARY_SUFFIX) -m

.PHONY: igloo-tests
igloo-tests: $(OUTPUT_DIR)/CMakeFiles 
	@cmake --build $(OUTPUT_DIR) --target igloo-tests
	$(OUTPUT_DIR)/tests/igloo/$(BINARY_DIR)/igloo-tests$(BINARY_SUFFIX)

.PHONY: specs-junit
specs-junit: $(REPORT_DIR)
	@cmake --build $(OUTPUT_DIR) --target specs
	$(OUTPUT_DIR)/tests/spec/$(BINARY_DIR)/specs$(BINARY_SUFFIX) -m -o junit --report-dir '$(REPORT_DIR)/tests/'

.PHONY: build-features
build-features: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target features

.PHONY: launch-features
launch-features: build-features
	$(LAUNCH_PREFIX) $(OUTPUT_DIR)/tests/feature/$(BINARY_DIR)/features$(BINARY_SUFFIX) $(LAUNCH_SUFFIX)

.PHONY: features
features: launch-features
	$(CUCUMBER) 

.PHONY: wip-features
wip-features: launch-features
	$(CUCUMBER) --profile wip 

.PHONY: features-doc
features-doc: launch-features
	$(CUCUMBER) --profile html

.PHONY: coverage-unittests 
coverage-unittests: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target coverage_tests

.PHONY: coverage-specs 
coverage-specs: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target coverage_specs

.PHONY: coverage-igloo 
coverage-igloo: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target coverage_igloo

.PHONY: coverage-features
coverage-features: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target coverage_features

.PHONY: coverage
coverage: $(REPORT_DIR) coverage-unittests coverage-features coverage-igloo coverage-specs

.PHONY: memcheck
memcheck: build-features
	$(LAUNCH_PREFIX) $(MEMCHECK) $(OUTPUT_DIR)/tests/feature/$(BINARY_DIR)/features$(BINARY_SUFFIX) $(LAUNCH_SUFFIX)
	sleep 10
	$(CUCUMBER)

.PHONY: cppcheck
cppcheck: $(REPORT_DIR)
	cppcheck -iexternals --enable=style -f --std=c++11 -j2 --xml --suppress=*:externals/include/gtest/gtest.h --suppress=*:externals/include/gtest/internal/gtest-tuple.h --suppress=*:externals/include/gmock/gmock.h ./ 2> $(REPORT_DIR)/cppcheck.xml

.PHONY: rats
rats: $(REPORT_DIR)
	rats --quiet --xml ./src > $(REPORT_DIR)/rats.xml

.PHONY: clean
clean: 
	@cmake --build $(OUTPUT_DIR) --target clean
	rm -rf $(OUTPUT_DIR)

.PHONY: clean-full
clean-full: clean 
	rm -rf ./externals/lib
	rm -rf ./externals/include


.PHONY: clean-reports
clean-reports: 
	rm -rf $(REPORT_DIR)

.PHONY: sonar-runner
sonar-runner: clean-reports cppcheck rats coverage memcheck
	sonar-runner

.PHONY: doc
doc: $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target doc

.PHONY: install
install:  $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target install

.PHONY: package
package:  $(OUTPUT_DIR)/CMakeFiles
	@cmake --build $(OUTPUT_DIR) --target package