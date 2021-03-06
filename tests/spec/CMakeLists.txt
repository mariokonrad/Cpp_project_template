# required minimum version of cmake
cmake_minimum_required(VERSION 3.2 FATAL_ERROR)

# set the path to the additional cmake modules
set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../../cmake/modules)

# set path to externals
set(CMAKE_INCLUDE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../../externals/include)
set(CMAKE_LIBRARY_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../../externals/lib)

# set report and documentation output paths
set(REPORT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../reports CACHE PATH "Reports directory")
set(COVERAGE_REPORT_DIR ${REPORT_DIR}/coverage CACHE PATH "Coverage reports output directory" )
set(TESTS_REPORT_DIR ${REPORT_DIR}/tests CACHE PATH "Testresult output directory" )

# create report and documentation output directories
file(MAKE_DIRECTORY
    ${REPORT_DIR}
    ${COVERAGE_REPORT_DIR}
    ${TESTS_REPORT_DIR}
)

option(USE_STATIC_BOOST "Statically link Boost" ${WIN32})

# Check for clang compiler
if(CMAKE_CXX_COMPILER MATCHES ".*clang")
  set(CMAKE_COMPILER_IS_CLANGCXX 1)
endif()

#########################################################################
# Create test executables for every testclass (no coverage measurement) #
#########################################################################

find_package(CppSpec REQUIRED)

if(NOT TARGET internal::projectlib)
    include(${CMAKE_CURRENT_SOURCE_DIR}/../../project-export.cmake)
endif()

set(CORE_BOOST_LIBS regex program_options filesystem date_time chrono thread system)
find_package(Boost COMPONENTS  ${CORE_BOOST_LIBS} REQUIRED)

add_executable(spectests
    src/dummy_spec.cpp
    src/specs.cpp
)


function(register_test TEST_FILE)
    get_filename_component(TEST_NAME ${TEST_FILE} NAME)
    message(STATUS "Adding spec " ${TEST_NAME})
    cppspec_add_tests(spectests "" include/${TEST_FILE}.h)
endfunction()

register_test(dummy_spec)

add_executable(tests::spec ALIAS spectests)

target_include_directories(spectests
    SYSTEM
    PRIVATE
        ${CPPSPEC_INCLUDE_DIRS}
)

target_include_directories(spectests
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

if(CMAKE_COMPILER_IS_CLANGCXX)
    target_compile_options(spectests
        PRIVATE
            -Wno-weak-vtables
            -Wno-exit-time-destructors

    )
endif(CMAKE_COMPILER_IS_CLANGCXX)

target_link_libraries(spectests
    ${CPPSPEC_LIBRARIES}
    ${Boost_LIBRARIES}
    internal::projectlib
)

if(USE_STATIC_BOOST)
  set(Boost_USE_STATIC_LIBS ON)
else(USE_STATIC_BOOST)
    target_compile_definitions(spectests
        PRIVATE
            BOOST_ALL_DYN_LINK
    )
endif(USE_STATIC_BOOST)

target_compile_definitions(spectests
    PRIVATE
        ${Boost_LIB_DIAGNOSTIC_DEFINITIONS}
)

# run allways catch tests target when make all
add_custom_target(run_spectests
    ALL
        spectests -m
)

add_dependencies(run_spectests
    tests::spec
)

add_custom_target(run_spectests-junit
    spectests -m -o junit --report-dir ${TESTS_REPORT_DIR}/tests/
)

add_dependencies(run_spectests-junit
    tests::spec
)

####################################################################
# Create and run a single test executable including all testclass. #
# With coverage measurement                                        #
####################################################################
if(UNIX AND CMAKE_COMPILER_IS_GNUCXX AND CMAKE_BUILD_TYPE MATCHES Debug)
    include(CodeCoverage)

    add_executable(spectests-cov
        EXCLUDE_FROM_ALL
            ${CPPSPECTEST_SOURCES}
            src/dummy_spec.cpp
            src/specs.cpp
    )

    if(CMAKE_COMPILER_IS_CLANGCXX)
        target_compile_options(spectests-cov
            PRIVATE
                -Wno-weak-vtables
                -Wno-exit-time-destructors

        )
    endif(CMAKE_COMPILER_IS_CLANGCXX)

    target_include_directories(spectests-cov
        SYSTEM
        PRIVATE
            ${CPPSPEC_INCLUDE_DIRS}
    )

    target_include_directories(spectests-cov
        PRIVATE
            ${CMAKE_CURRENT_SOURCE_DIR}/include
    )

    target_link_libraries(spectests-cov
        ${CPPSPEC_LIBRARIES}
        ${Boost_LIBRARIES}
        internal::projectlib-cov
    )

    if(USE_STATIC_BOOST)
      set(Boost_USE_STATIC_LIBS ON)
    else(USE_STATIC_BOOST)
        target_compile_definitions(spectests-cov
            PRIVATE
                BOOST_ALL_DYN_LINK
        )
    endif(USE_STATIC_BOOST)

    target_compile_definitions(spectests-cov
        PRIVATE
            ${Boost_LIB_DIAGNOSTIC_DEFINITIONS}
    )

    setup_target_for_coverage_cobertura(coverage_specs
      spectests-cov
      ${COVERAGE_REPORT_DIR}/specifications
      "-m;-ojunit;--report-dir;'${TESTS_REPORT_DIR}/'"
     )
endif(UNIX AND CMAKE_COMPILER_IS_GNUCXX AND CMAKE_BUILD_TYPE MATCHES Debug)

